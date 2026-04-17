"""Database access helpers for the adaptive-learning workflow.

The adaptive agent is mostly deterministic, but it still needs live data from
MongoDB to be useful in production:

- a learner profile to continue the student's progression
- a question bank (optionally scoped by exam or topics) to rank candidates

This module isolates that persistence logic so the adaptive core remains easy to
unit test by swapping in a fake repository.
"""

from __future__ import annotations

import os
from collections.abc import Iterable, Sequence
from typing import Any

try:  # pragma: no cover - optional in lightweight test environments
    from motor.motor_asyncio import AsyncIOMotorClient
except Exception:  # pragma: no cover - fallback when motor is unavailable
    AsyncIOMotorClient = None

try:  # pragma: no cover - import availability depends on pymongo install
    from bson import ObjectId
except Exception:  # pragma: no cover - defensive fallback
    ObjectId = None

from master.agents.common.learner_profile import LearnerProfile
from master.agents.common.message import ExamQuestion


class AdaptiveDBTools:
    """Repository-like helpers for adaptive question/profile persistence."""

    def __init__(
        self,
        *,
        mongo_uri: str | None = None,
        mongo_client: AsyncIOMotorClient | None = None,
        database_name: str | None = None,
        question_collection: str | None = None,
        exam_collection: str | None = None,
        learner_profile_collection: str | None = None,
        history_collection: str | None = None,
    ) -> None:
        """Create a Mongo-backed toolset for the adaptive agent."""

        resolved_uri = mongo_uri or os.getenv("MONGO_URI")
        self._client = mongo_client
        if self._client is None and resolved_uri and AsyncIOMotorClient is not None:
            self._client = AsyncIOMotorClient(resolved_uri)
        self.database_name = database_name or os.getenv("ADAPTIVE_DB_NAME") or "masterthpt"
        self.question_collection = (
            question_collection
            or os.getenv("ADAPTIVE_QUESTION_COLLECTION")
            or "questions"
        )
        self.exam_collection = (
            exam_collection
            or os.getenv("ADAPTIVE_EXAM_COLLECTION")
            or "exams"
        )
        self.learner_profile_collection = (
            learner_profile_collection
            or os.getenv("ADAPTIVE_PROFILE_COLLECTION")
            or "learner_profiles"
        )
        self.history_collection = (
            history_collection
            or os.getenv("ADAPTIVE_HISTORY_COLLECTION")
            or "histories"
        )

    def _require_client(self) -> AsyncIOMotorClient:
        """Return the configured Mongo client or raise a clear configuration error."""

        if self._client is None:
            raise RuntimeError(
                "AdaptiveDBTools requires motor + MONGO_URI (or an injected "
                "mongo_client) before it can query Questions/LearnerProfile data."
            )
        return self._client

    def _collection(self, collection_name: str):
        """Return a Mongo collection handle from the configured database."""

        return self._require_client()[self.database_name][collection_name]

    @staticmethod
    def _valid_object_ids(ids: Sequence[str]) -> list[Any]:
        """Convert valid 24-char ids to ``ObjectId`` instances when available."""

        if ObjectId is None:
            return []
        return [ObjectId(item) for item in ids if ObjectId.is_valid(item)]

    @classmethod
    def _build_any_id_filter(cls, ids: Sequence[str]) -> dict[str, Any] | None:
        """Build a Mongo filter that matches either ``id`` or ``_id``."""

        unique_ids = []
        seen: set[str] = set()
        for item in ids:
            if not item or item in seen:
                continue
            seen.add(item)
            unique_ids.append(item)

        if not unique_ids:
            return None

        object_ids = cls._valid_object_ids(unique_ids)
        or_filters: list[dict[str, Any]] = []

        if len(unique_ids) == 1:
            or_filters.append({"id": unique_ids[0]})
            if object_ids:
                or_filters.append({"_id": object_ids[0]})
        else:
            or_filters.append({"id": {"$in": unique_ids}})
            if object_ids:
                or_filters.append({"_id": {"$in": object_ids}})

        if len(or_filters) == 1:
            return or_filters[0]
        return {"$or": or_filters}

    @staticmethod
    def _normalize_question_document(document: dict[str, Any]) -> ExamQuestion:
        """Normalize a raw Mongo document into the shared ``ExamQuestion`` model."""

        payload = dict(document)
        mongo_id = payload.pop("_id", None)
        if "id" not in payload and mongo_id is not None:
            payload["id"] = str(mongo_id)
        return ExamQuestion.model_validate(payload)

    async def get_learner_profile(self, student_id: str) -> LearnerProfile | None:
        """Fetch a persisted learner profile by ``student_id``."""

        document = await self._collection(self.learner_profile_collection).find_one(
            {"student_id": student_id},
            projection={"_id": 0},
        )
        if not document:
            return None
        return LearnerProfile.model_validate(document)

    async def upsert_learner_profile(self, profile: LearnerProfile) -> None:
        """Persist the latest learner profile snapshot with upsert semantics."""

        await self._collection(self.learner_profile_collection).update_one(
            {"student_id": profile.student_id},
            {"$set": profile.model_dump(mode="json")},
            upsert=True,
        )

    async def get_exam_question_ids(self, exam_id: str) -> list[str]:
        """Resolve an exam document to the ordered list of question ids it references."""

        exam_filter = self._build_any_id_filter([exam_id])
        if exam_filter is None:
            return []

        document = await self._collection(self.exam_collection).find_one(
            exam_filter,
            projection={"questions": 1},
        )
        raw_ids = document.get("questions", []) if document else []
        return [item for item in raw_ids if isinstance(item, str) and item.strip()]

    async def get_history_by_id(self, history_id: str) -> dict[str, Any] | None:
        """Fetch one history document by Mongo id string."""

        history_filter = self._build_any_id_filter([history_id])
        if history_filter is None:
            return None
        return await self._collection(self.history_collection).find_one(history_filter)

    async def get_latest_history(
        self,
        *,
        user_id: str,
        exam_id: str | None = None,
    ) -> dict[str, Any] | None:
        """Fetch the latest history document for a user, optionally scoped by exam."""

        mongo_filter: dict[str, Any] = {"user_id": user_id}
        if exam_id:
            mongo_filter["exam_id"] = exam_id

        cursor = self._collection(self.history_collection).find(mongo_filter).sort(
            [("created_at", -1), ("_id", -1)]
        )
        documents = await cursor.to_list(length=1)
        return documents[0] if documents else None

    async def get_questions(
        self,
        *,
        exam_id: str | None = None,
        question_ids: Sequence[str] | None = None,
        topic_tags: Sequence[str] | None = None,
        exclude_question_ids: Sequence[str] | None = None,
        limit: int = 100,
    ) -> list[ExamQuestion]:
        """Fetch candidate questions from MongoDB for adaptive ranking."""

        effective_question_ids = list(question_ids or [])
        if exam_id and not effective_question_ids:
            effective_question_ids = await self.get_exam_question_ids(exam_id)

        mongo_filter: dict[str, Any] = {}
        and_filters: list[dict[str, Any]] = []

        if effective_question_ids:
            any_id_filter = self._build_any_id_filter(effective_question_ids)
            if any_id_filter:
                and_filters.append(any_id_filter)

        normalized_topics = [topic for topic in (topic_tags or []) if topic]
        if normalized_topics:
            and_filters.append({"topic_tags": {"$in": normalized_topics}})

        if and_filters:
            mongo_filter = and_filters[0] if len(and_filters) == 1 else {"$and": and_filters}

        cursor = self._collection(self.question_collection).find(mongo_filter)
        if not effective_question_ids and limit > 0:
            cursor = cursor.limit(int(limit))

        documents = await cursor.to_list(length=None)
        questions = [
            self._normalize_question_document(document)
            for document in documents
        ]

        excluded = {question_id for question_id in (exclude_question_ids or []) if question_id}
        if excluded:
            questions = [
                question
                for question in questions
                if question.question_id not in excluded
            ]

        if effective_question_ids:
            order = {question_id: index for index, question_id in enumerate(effective_question_ids)}
            questions.sort(key=lambda question: order.get(question.question_id, len(order)))
        return questions

    async def get_rag_question_context(
        self,
        *,
        exam_id: str | None = None,
        question_ids: Sequence[str] | None = None,
        topic_tags: Sequence[str] | None = None,
        exclude_question_ids: Sequence[str] | None = None,
        limit: int = 8,
    ) -> list[ExamQuestion]:
        """Retrieve style/context questions that ground adaptive generation.

        This is intentionally a thin semantic wrapper around ``get_questions`` so
        callers can express that these results are RAG context, not the final
        selected/generated output.
        """

        return await self.get_questions(
            exam_id=exam_id,
            question_ids=question_ids,
            topic_tags=topic_tags,
            exclude_question_ids=exclude_question_ids,
            limit=limit,
        )
