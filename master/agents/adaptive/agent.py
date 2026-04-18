"""Lightweight wrapper around the deterministic adaptive service.

The adaptive core is still deterministic, but this wrapper exposes it as a
LangGraph subgraph so the manager/orchestrator can pass shared state through it
before handing work to other agents.
"""

from __future__ import annotations

import asyncio
import threading
from typing import Any

from langgraph.graph import END, START, StateGraph
from master.agents.common.agent_logging import log_agent_event
from master.agents.common.learner_profile import LearnerProfile
from master.agents.common.langsmith import build_langsmith_invoke_config
from master.agents.common.message import ExamQuestion, MessageRequest, StudentAnswer
from typing_extensions import TypedDict

from .db_tools import AdaptiveDBTools
from .generator import AdaptiveQuestionGenerator
from .profile_builder import AdaptiveAttempt
from .question_gen import QuestionRecommendation
from .service import AdaptiveService


class AdaptiveWorkflowState(TypedDict, total=False):
    request: MessageRequest
    learner_profile: LearnerProfile
    questions: list[ExamQuestion]
    rag_context_questions: list[ExamQuestion]
    generated_questions: list[ExamQuestion]
    student_answers: list[StudentAnswer]
    selected_questions: list[ExamQuestion]
    profile_updates: dict[str, Any]


class AdaptiveAgent:
    """Adaptive agent exposed as a LangGraph workflow plus convenience methods."""

    def __init__(
        self,
        service: AdaptiveService | None = None,
        repository: AdaptiveDBTools | None = None,
        generator: AdaptiveQuestionGenerator | None = None,
    ) -> None:
        """Create the adaptive LangGraph wrapper around ``AdaptiveService``.

        Args:
            service: Optional injected adaptive service.
            repository: Optional database toolset used to fetch questions and
                persist/load learner profiles.
            generator: Optional LLM-backed question generator for adaptive
                generation mode.
        """

        self.service = service or AdaptiveService()
        self.repository = repository or AdaptiveDBTools()
        self.generator = generator or AdaptiveQuestionGenerator()
        self.graph = self._build_graph()
        log_agent_event(
            "adaptive",
            "initialized",
            extra={
                "service": type(self.service).__name__,
                "repository": type(self.repository).__name__,
                "generator": type(self.generator).__name__,
            },
            mode="completed",
        )

    @staticmethod
    def _sync_await(coro):
        """Run an async helper from the sync LangGraph nodes used by the agent."""

        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(coro)

        result: dict[str, Any] = {}
        error: dict[str, BaseException] = {}

        def _runner() -> None:
            try:
                result["value"] = asyncio.run(coro)
            except BaseException as exc:  # pragma: no cover - defensive bridge
                error["value"] = exc

        thread = threading.Thread(target=_runner, daemon=True)
        thread.start()
        thread.join()

        if "value" in error:
            raise error["value"]
        return result.get("value")

    def _build_graph(self):
        """Compile the three-step adaptive workflow into a LangGraph subgraph."""

        builder = StateGraph(AdaptiveWorkflowState)
        builder.add_node("ensure_profile", self._ensure_profile_node)
        builder.add_node("update_profile", self._update_profile_node)
        builder.add_node("recommend_questions", self._recommend_questions_node)

        builder.add_edge(START, "ensure_profile")
        builder.add_edge("ensure_profile", "update_profile")
        builder.add_edge("update_profile", "recommend_questions")
        builder.add_edge("recommend_questions", END)
        graph = builder.compile()
        log_agent_event("adaptive", "graph_compiled", mode="completed")
        return graph

    @staticmethod
    def _normalize_answer(value: str | None) -> str:
        """Normalize an answer string for lightweight exact-match comparison."""

        return (value or "").strip().upper().replace(" ", "")

    def _is_answer_correct(
        self,
        student_answer: str | None,
        correct_answer: str | None,
    ) -> bool:
        """Apply a lightweight correctness check for adaptive-profile updates."""

        return self._normalize_answer(student_answer) == self._normalize_answer(
            correct_answer
        )

    def _ensure_profile_node(self, state: AdaptiveWorkflowState) -> dict[str, Any]:
        """Ensure the workflow state always carries a learner profile.

        Args:
            state: Current adaptive workflow state.

        Returns:
            A state patch that either preserves the injected profile or creates
            a new one from request identifiers.
        """

        profile = state.get("learner_profile")
        request = state.get("request")
        log_agent_event(
            "adaptive",
            "ensure_profile:start",
            state=state,
            request=request,
            mode="agent_node",
        )
        if profile is not None:
            log_agent_event(
                "adaptive",
                "ensure_profile:existing_profile",
                state=state,
                request=request,
                mode="progress",
            )
            return {"learner_profile": profile}

        request = state.get("request")
        student_id = "anonymous"
        if request is not None:
            student_id = request.student_id or request.user_id or student_id

        loaded_profile = None
        if student_id != "anonymous":
            loaded_profile = self.load_learner_profile(student_id)
        if loaded_profile is not None:
            log_agent_event(
                "adaptive",
                "ensure_profile:loaded_profile",
                request=request,
                extra={"student_id": student_id},
                mode="completed",
            )
            return {"learner_profile": loaded_profile}

        created_profile = self.service.create_profile(student_id)
        if student_id != "anonymous":
            self.save_learner_profile(created_profile)
        log_agent_event(
            "adaptive",
            "ensure_profile:created_profile",
            request=request,
            extra={"student_id": student_id},
            mode="completed",
        )
        return {"learner_profile": created_profile}

    def _update_profile_node(self, state: AdaptiveWorkflowState) -> dict[str, Any]:
        """Transform graded answers into attempts and replay them into the profile.

        Args:
            state: Current adaptive workflow state.

        Returns:
            A state patch containing the updated learner profile and a compact
            audit summary of what changed.
        """

        profile = state.get("learner_profile")
        request = state.get("request")
        log_agent_event(
            "adaptive",
            "update_profile:start",
            state=state,
            request=request,
            mode="agent_node",
        )
        questions = [ExamQuestion.model_validate(question) for question in state.get("questions", [])]
        answers = [StudentAnswer.model_validate(answer) for answer in state.get("student_answers", [])]
        question_map = {question.question_id: question for question in questions}

        attempts: list[AdaptiveAttempt] = []
        for answer in answers:
            question = question_map.get(answer.question_id)
            if question is None or not answer.normalized_answer():
                continue
            attempts.append(
                AdaptiveAttempt.from_question(
                    question,
                    is_correct=self._is_answer_correct(
                        answer.normalized_answer(),
                        question.correct_answer,
                    ),
                )
            )

        if not attempts or profile is None:
            no_update_result = {
                "profile_updates": {
                    "attempts_processed": 0,
                    "weak_topics": profile.weak_topics() if profile else [],
                    "strong_topics": profile.strong_topics() if profile else [],
                }
            }
            log_agent_event(
                "adaptive",
                "update_profile:no_attempts",
                state=state,
                request=request,
                extra={"attempts": len(attempts)},
                mode="warning",
            )
            return no_update_result

        updated_profile, summaries = self.service.update_profile_from_attempts(
            profile,
            attempts,
        )
        self.save_learner_profile(updated_profile)
        update_result = {
            "learner_profile": updated_profile,
            "profile_updates": {
                "attempts_processed": len(attempts),
                "updates": summaries,
                "weak_topics": updated_profile.weak_topics(),
                "strong_topics": updated_profile.strong_topics(),
            },
        }
        log_agent_event(
            "adaptive",
            "update_profile:done",
            request=request,
            extra={
                "attempts": len(attempts),
                "summary_count": len(summaries),
                "weak_topics": len(updated_profile.weak_topics()),
                "strong_topics": len(updated_profile.strong_topics()),
            },
            mode="completed",
        )
        return update_result

    def _recommend_questions_node(self, state: AdaptiveWorkflowState) -> dict[str, Any]:
        """Score the current question bank and select the next adaptive items.

        Args:
            state: Current adaptive workflow state.

        Returns:
            A state patch containing the selected next questions.
        """

        profile = state.get("learner_profile")
        request = state.get("request")
        log_agent_event(
            "adaptive",
            "recommend_questions:start",
            state=state,
            request=request,
            mode="agent_node",
        )
        answers = [StudentAnswer.model_validate(answer) for answer in state.get("student_answers", [])]
        answered_question_ids = [answer.question_id for answer in answers if answer.question_id]
        questions = [ExamQuestion.model_validate(question) for question in state.get("questions", [])]

        if profile is None:
            log_agent_event(
                "adaptive",
                "recommend_questions:missing_profile",
                state=state,
                request=request,
                mode="warning",
            )
            return {"selected_questions": []}

        if self.should_generate_questions(request):
            rag_context_questions = self.load_rag_context_questions(
                request=request,
                profile=profile,
                exclude_question_ids=answered_question_ids,
            )
            if not rag_context_questions:
                log_agent_event(
                    "adaptive",
                    "recommend_questions:no_rag_context",
                    request=request,
                    extra={"answered_questions": len(answered_question_ids)},
                    mode="warning",
                )
                return {
                    "rag_context_questions": [],
                    "generated_questions": [],
                    "selected_questions": [],
                }

            generated_questions = self.generate_questions_from_context(
                request=request,
                profile=profile,
                rag_context_questions=rag_context_questions,
            )
            generation_result = {
                "rag_context_questions": rag_context_questions,
                "generated_questions": generated_questions,
                "selected_questions": generated_questions,
            }
            log_agent_event(
                "adaptive",
                "recommend_questions:generated",
                request=request,
                extra={
                    "rag_context_questions": len(rag_context_questions),
                    "generated_questions": len(generated_questions),
                },
                mode="completed",
            )
            return generation_result

        if not questions:
            questions = self.load_questions(
                request=request,
                profile=profile,
                exclude_question_ids=answered_question_ids,
            )
            if not questions:
                log_agent_event(
                    "adaptive",
                    "recommend_questions:no_candidates",
                    request=request,
                    extra={"answered_questions": len(answered_question_ids)},
                    mode="warning",
                )
                return {"questions": [], "selected_questions": []}

        selected = self.service.select_questions(
            profile,
            questions,
            limit=min(5, len(questions)),
            exclude_question_ids=answered_question_ids,
        )
        result = {"questions": questions, "selected_questions": selected}
        log_agent_event(
            "adaptive",
            "recommend_questions:selected",
            request=request,
            extra={
                "candidate_questions": len(questions),
                "selected_questions": len(selected),
            },
            mode="completed",
        )
        return result

    def run(self, state: AdaptiveWorkflowState) -> AdaptiveWorkflowState:
        """Invoke the LangGraph adaptive workflow on a shared state dict."""

        log_agent_event(
            "adaptive",
            "run:start",
            state=state,
            request=state.get("request"),
            mode="agent_node",
        )
        final_state = self.graph.invoke(
            state,
            config=build_langsmith_invoke_config(
                run_name="AdaptiveAgent.run",
                agent_role="adaptive",
                extra_tags=["adaptive", "question-selection"],
            ),
        )
        log_agent_event(
            "adaptive",
            "run:done",
            state=final_state,
            request=final_state.get("request"),
            mode="completed",
        )
        return final_state

    def load_learner_profile(self, student_id: str) -> LearnerProfile | None:
        """Load the persisted learner profile from the adaptive profile store."""

        try:
            profile = self._sync_await(self.repository.get_learner_profile(student_id))
            log_agent_event(
                "adaptive",
                "load_learner_profile",
                extra={"student_id": student_id, "found": profile is not None},
                mode="progress",
            )
            return profile
        except RuntimeError:
            log_agent_event(
                "adaptive",
                "load_learner_profile_failed",
                extra={"student_id": student_id},
                mode="warning",
            )
            return None

    def save_learner_profile(self, profile: LearnerProfile) -> None:
        """Persist the latest learner profile snapshot to the adaptive profile store."""

        try:
            self._sync_await(self.repository.upsert_learner_profile(profile))
            log_agent_event(
                "adaptive",
                "save_learner_profile",
                extra={"student_id": profile.student_id},
                mode="progress",
            )
        except RuntimeError:
            log_agent_event(
                "adaptive",
                "save_learner_profile_failed",
                extra={"student_id": profile.student_id},
                mode="warning",
            )
            return None

    def load_questions(
        self,
        *,
        request: MessageRequest | None,
        profile: LearnerProfile,
        exclude_question_ids: list[str] | None = None,
    ) -> list[ExamQuestion]:
        """Fetch candidate questions from MongoDB for adaptive selection.

        The loader supports a few progressively stronger filters:

        1. ``request.exam_id`` or explicit ``metadata.question_ids``
        2. ``metadata.topic_tags``
        3. weak topics derived from the current learner profile
        """

        metadata = request.metadata if request else {}
        requested_question_ids = metadata.get("question_ids") or []
        requested_topic_tags = metadata.get("topic_tags") or profile.weak_topics()
        requested_limit = metadata.get("question_limit") or metadata.get("limit") or 100

        if not isinstance(requested_question_ids, list):
            requested_question_ids = []
        if not isinstance(requested_topic_tags, list):
            requested_topic_tags = []

        try:
            limit = max(1, int(requested_limit))
        except (TypeError, ValueError):
            limit = 100

        try:
            questions = self._sync_await(
                self.repository.get_questions(
                    exam_id=request.exam_id if request else None,
                    question_ids=requested_question_ids,
                    topic_tags=requested_topic_tags,
                    exclude_question_ids=exclude_question_ids or [],
                    limit=limit,
                )
            )
            log_agent_event(
                "adaptive",
                "load_questions",
                request=request,
                extra={
                    "question_ids": len(requested_question_ids),
                    "topic_tags": len(requested_topic_tags),
                    "exclude_question_ids": len(exclude_question_ids or []),
                    "limit": limit,
                    "result": len(questions),
                },
                mode="progress",
            )
            return questions
        except RuntimeError:
            log_agent_event(
                "adaptive",
                "load_questions_failed",
                request=request,
                extra={"limit": limit},
                mode="warning",
            )
            return []

    def load_rag_context_questions(
        self,
        *,
        request: MessageRequest | None,
        profile: LearnerProfile,
        exclude_question_ids: list[str] | None = None,
    ) -> list[ExamQuestion]:
        """Always retrieve DB-backed question context for adaptive generation."""

        metadata = request.metadata if request else {}
        requested_question_ids = metadata.get("rag_question_ids") or metadata.get("question_ids") or []
        requested_topic_tags = metadata.get("rag_topic_tags") or metadata.get("topic_tags") or profile.weak_topics()
        requested_limit = metadata.get("rag_context_limit") or 8

        if not isinstance(requested_question_ids, list):
            requested_question_ids = []
        if not isinstance(requested_topic_tags, list):
            requested_topic_tags = []

        try:
            limit = max(1, int(requested_limit))
        except (TypeError, ValueError):
            limit = 8

        try:
            questions = self._sync_await(
                self.repository.get_rag_question_context(
                    exam_id=request.exam_id if request else None,
                    question_ids=requested_question_ids,
                    topic_tags=requested_topic_tags,
                    exclude_question_ids=exclude_question_ids or [],
                    limit=limit,
                )
            )
            log_agent_event(
                "adaptive",
                "load_rag_context_questions",
                request=request,
                extra={
                    "question_ids": len(requested_question_ids),
                    "topic_tags": len(requested_topic_tags),
                    "exclude_question_ids": len(exclude_question_ids or []),
                    "limit": limit,
                    "result": len(questions),
                },
                mode="progress",
            )
            return questions
        except RuntimeError:
            log_agent_event(
                "adaptive",
                "load_rag_context_questions_failed",
                request=request,
                extra={"limit": limit},
                mode="warning",
            )
            return []

    @staticmethod
    def should_generate_questions(request: MessageRequest | None) -> bool:
        """Return whether the current request asks adaptive to generate new items."""

        if request is None:
            return False

        metadata = request.metadata or {}
        mode = str(metadata.get("adaptive_mode") or "").strip().lower()
        return bool(metadata.get("generate_questions")) or mode in {
            "generate",
            "generate_questions",
            "rag_generate",
        }

    def generate_questions_from_context(
        self,
        *,
        request: MessageRequest | None,
        profile: LearnerProfile,
        rag_context_questions: list[ExamQuestion],
    ) -> list[ExamQuestion]:
        """Generate new practice questions from mandatory DB-retrieved context."""

        metadata = request.metadata if request else {}
        requested_limit = metadata.get("generation_limit") or metadata.get("question_limit") or 3
        try:
            limit = max(1, int(requested_limit))
        except (TypeError, ValueError):
            limit = 3

        generated = self.generator.generate_questions(
            request=request,
            profile=profile,
            context_questions=rag_context_questions,
            limit=limit,
        )
        log_agent_event(
            "adaptive",
            "generate_questions_from_context",
            request=request,
            extra={
                "context_questions": len(rag_context_questions),
                "limit": limit,
                "generated": len(generated),
            },
            mode="completed",
        )
        return generated

    def update_profile(
        self,
        profile: LearnerProfile,
        attempt: AdaptiveAttempt,
    ) -> tuple[LearnerProfile, dict]:
        """Delegate one attempt update to the underlying adaptive service."""

        return self.service.update_profile(profile, attempt)

    def recommend_questions(
        self,
        profile: LearnerProfile,
        questions: list[ExamQuestion],
        *,
        limit: int = 5,
    ) -> list[QuestionRecommendation]:
        """Delegate question ranking to the underlying adaptive service."""

        return self.service.recommend_questions(profile, questions, limit=limit)
