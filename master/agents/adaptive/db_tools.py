"""Adaptive repository backed by the shared MongoDB helpers."""

from __future__ import annotations

import os
from typing import Any, Iterable

from bson import ObjectId

from master.agents.common.learner_profile import LearnerProfile
from master.agents.common.message import ExamQuestion
from master.agents.common.tools import MongoDBTools


class AdaptiveDBTools(MongoDBTools):
    """Mongo-backed repository for adaptive and manager flows.

    This class intentionally builds on the shared DB helpers exposed through
    `master.agents.common.tools`, so future agents can reuse the same access
    pattern instead of creating their own Mongo clients.
    """

    def __init__(
        self,
        database_name: str | None = None,
        question_collection: str | None = None,
        exam_collection: str | None = None,
        profile_collection: str | None = None,
        history_collection: str | None = None,
    ) -> None:
        self.database_name = (
            database_name
            or os.getenv("ADAPTIVE_DB_NAME")
            or os.getenv("MONGO_DB_NAME")
            or "masterthpt"
        )
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
        self.profile_collection = (
            profile_collection
            or os.getenv("ADAPTIVE_PROFILE_COLLECTION")
            or "learner_profiles"
        )
        self.history_collection = (
            history_collection
            or os.getenv("ADAPTIVE_HISTORY_COLLECTION")
            or "histories"
        )
        self._profile_schema_ready = False

    def _learner_profile_validator(self) -> dict[str, Any]:
        return {
            "$jsonSchema": {
                "bsonType": "object",
                "required": [
                    "student_id",
                    "theta",
                    "total_attempts",
                    "total_correct",
                    "topic_mastery",
                    "topic_attempts",
                    "topic_correct",
                    "recent_question_ids",
                    "recent_topics",
                ],
                "properties": {
                    "student_id": {"bsonType": "string", "description": "Stable learner identifier"},
                    "theta": {"bsonType": ["double", "int", "long", "decimal"], "description": "Global ability estimate"},
                    "total_attempts": {"bsonType": ["int", "long"], "minimum": 0},
                    "total_correct": {"bsonType": ["int", "long"], "minimum": 0},
                    "topic_mastery": {"bsonType": "object"},
                    "topic_attempts": {"bsonType": "object"},
                    "topic_correct": {"bsonType": "object"},
                    "recent_question_ids": {
                        "bsonType": "array",
                        "items": {"bsonType": "string"},
                    },
                    "recent_topics": {
                        "bsonType": "array",
                        "items": {"bsonType": "string"},
                    },
                    "last_updated_question_id": {
                        "bsonType": ["string", "null"],
                    },
                },
            }
        }

    async def ensure_learner_profile_schema(self) -> None:
        if self._profile_schema_ready:
            return

        database = self.get_mongo_client()[self.database_name]
        collection_names = await database.list_collection_names()
        validator = self._learner_profile_validator()

        if self.profile_collection not in collection_names:
            await database.create_collection(
                self.profile_collection,
                validator=validator,
                validationLevel="strict",
            )
        else:
            try:
                await database.command(
                    {
                        "collMod": self.profile_collection,
                        "validator": validator,
                        "validationLevel": "strict",
                    }
                )
            except Exception:
                # Some Mongo-compatible providers do not support collMod.
                # In that case we still create the index below and continue.
                pass

        collection = database[self.profile_collection]
        await collection.create_index("student_id", unique=True, name="student_id_unique")
        self._profile_schema_ready = True

    @staticmethod
    def _clean_values(values: Iterable[str] | None) -> list[str]:
        if not values:
            return []
        unique: list[str] = []
        
        seen: set[str] = set()
        for value in values:
            normalized = str(value).strip()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            unique.append(normalized)
        return unique

    @staticmethod
    def _to_object_ids(values: Iterable[str]) -> list[ObjectId]:
        return [ObjectId(value) for value in values if ObjectId.is_valid(value)]

    @classmethod
    def _build_any_id_filter(cls, values: Iterable[str] | None) -> dict[str, Any] | None:
        normalized = cls._clean_values(values)
        if not normalized:
            return None

        object_ids = cls._to_object_ids(normalized)
        if len(normalized) == 1:
            if object_ids:
                return {"$or": [{"id": normalized[0]}, {"_id": object_ids[0]}]}
            return {"id": normalized[0]}

        if object_ids:
            return {
                "$or": [
                    {"id": {"$in": normalized}},
                    {"_id": {"$in": object_ids}},
                ]
            }
        return {"id": {"$in": normalized}}

    @classmethod
    def _build_any_id_exclusion(
        cls,
        values: Iterable[str] | None,
    ) -> dict[str, Any] | None:
        normalized = cls._clean_values(values)
        if not normalized:
            return None

        object_ids = cls._to_object_ids(normalized)
        clauses: list[dict[str, Any]] = [{"id": {"$nin": normalized}}]
        if object_ids:
            clauses.append({"_id": {"$nin": object_ids}})
        if len(clauses) == 1:
            return clauses[0]
        return {"$and": clauses}

    @staticmethod
    def _merge_filters(*filters: dict[str, Any] | None) -> dict[str, Any]:
        active = [item for item in filters if item]
        if not active:
            return {}
        if len(active) == 1:
            return active[0]
        return {"$and": active}

    @staticmethod
    def _normalize_document(
        document: dict[str, Any] | None,
        *,
        exam_id: str | None = None,
    ) -> dict[str, Any] | None:
        if document is None:
            return None

        normalized = dict(document)
        mongo_id = normalized.get("_id")
        if mongo_id is not None:
            mongo_id_str = str(mongo_id)
            normalized["_id"] = mongo_id_str
            normalized.setdefault("mongo_id", mongo_id_str)
            normalized.setdefault("id", mongo_id_str)

        if exam_id and not normalized.get("exam_id"):
            normalized["exam_id"] = exam_id

        return normalized

    async def _get_exam_question_ids(self, exam_id: str | None) -> list[str]:
        if not exam_id:
            return []

        exam_filter = self._build_any_id_filter([exam_id])
        if exam_filter is None:
            return []

        exam_document = await self.get_one(
            self.database_name,
            self.exam_collection,
            exam_filter,
        )
        exam_document = self._normalize_document(exam_document)
        if exam_document is None:
            return []

        return self._clean_values(exam_document.get("questions"))

    async def get_learner_profile(self, student_id: str) -> LearnerProfile | None:
        await self.ensure_learner_profile_schema()
        document = await self.get_one(
            self.database_name,
            self.profile_collection,
            {"student_id": student_id},
        )
        normalized = self._normalize_document(document)
        if normalized is None:
            return None
        return LearnerProfile.model_validate(normalized)

    async def upsert_learner_profile(self, profile: LearnerProfile) -> int:
        await self.ensure_learner_profile_schema()
        payload = profile.model_dump(mode="json")
        return await self.upsert_one(
            self.database_name,
            self.profile_collection,
            {"student_id": profile.student_id},
            payload,
        )

    async def get_history_by_id(self, history_id: str) -> dict[str, Any] | None:
        history_filter = self._build_any_id_filter([history_id])
        if history_filter is None:
            return None

        document = await self.get_one(
            self.database_name,
            self.history_collection,
            history_filter,
        )
        return self._normalize_document(document)

    async def get_latest_history(
        self,
        user_id: str,
        exam_id: str | None = None,
    ) -> dict[str, Any] | None:
        query: dict[str, Any] = {"user_id": user_id}
        if exam_id:
            query["exam_id"] = exam_id

        collection = self._collection(self.database_name, self.history_collection)
        documents = await (
            collection.find(query)
            .sort([("created_at", -1), ("_id", -1)])
            .limit(1)
            .to_list(length=1)
        )
        if not documents:
            return None
        return self._normalize_document(documents[0])

    async def get_questions(
        self,
        *,
        exam_id: str | None = None,
        question_ids: list[str] | None = None,
        topic_tags: list[str] | None = None,
        exclude_question_ids: list[str] | None = None,
        limit: int = 100,
    ) -> list[ExamQuestion]:
        normalized_limit = max(1, int(limit))
        explicit_question_ids = self._clean_values(question_ids)
        requested_question_ids = self._clean_values(question_ids)
        requested_topic_tags = self._clean_values(topic_tags)
        exam_question_ids = await self._get_exam_question_ids(exam_id)

        if exam_id and not exam_question_ids and not requested_question_ids:
            return []

        if exam_question_ids:
            if requested_question_ids:
                allowed_ids = set(exam_question_ids)
                requested_question_ids = [
                    question_id
                    for question_id in requested_question_ids
                    if question_id in allowed_ids
                ]
            else:
                requested_question_ids = exam_question_ids

        if exam_id and explicit_question_ids and exam_question_ids and not requested_question_ids:
            return []

        if exam_id and exam_question_ids and not requested_question_ids and not requested_topic_tags:
            return []

        query = self._merge_filters(
            self._build_any_id_filter(requested_question_ids),
            {"topic_tags": {"$in": requested_topic_tags}} if requested_topic_tags else None,
            self._build_any_id_exclusion(exclude_question_ids),
        )

        documents = await self.get_data(
            self.database_name,
            self.question_collection,
            query,
            limit=normalized_limit,
        )

        questions: list[ExamQuestion] = []
        for document in documents:
            normalized = self._normalize_document(document, exam_id=exam_id)
            if normalized is None:
                continue
            questions.append(ExamQuestion.model_validate(normalized))

        if exam_question_ids:
            question_order = {question_id: index for index, question_id in enumerate(exam_question_ids)}
            questions.sort(key=lambda item: question_order.get(item.question_id, len(question_order)))
        else:
            questions.sort(key=lambda item: item.question_index)
        return questions

    async def get_rag_question_context(
        self,
        *,
        exam_id: str | None = None,
        question_ids: list[str] | None = None,
        topic_tags: list[str] | None = None,
        exclude_question_ids: list[str] | None = None,
        limit: int = 8,
    ) -> list[ExamQuestion]:
        return await self.get_questions(
            exam_id=exam_id,
            question_ids=question_ids,
            topic_tags=topic_tags,
            exclude_question_ids=exclude_question_ids,
            limit=limit,
        )
