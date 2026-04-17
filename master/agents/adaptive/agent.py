"""Lightweight wrapper around the deterministic adaptive service.

The adaptive core is still deterministic, but this wrapper exposes it as a
LangGraph subgraph so the manager/orchestrator can pass shared state through it
before handing work to other agents.
"""

from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph
from master.agents.common.learner_profile import LearnerProfile
from master.agents.common.message import ExamQuestion, MessageRequest, StudentAnswer
from typing_extensions import TypedDict

from .profile_builder import AdaptiveAttempt
from .question_gen import QuestionRecommendation
from .service import AdaptiveService


class AdaptiveWorkflowState(TypedDict, total=False):
    request: MessageRequest
    learner_profile: LearnerProfile
    questions: list[ExamQuestion]
    student_answers: list[StudentAnswer]
    selected_questions: list[ExamQuestion]
    profile_updates: dict[str, Any]


class AdaptiveAgent:
    """Adaptive agent exposed as a LangGraph workflow plus convenience methods."""

    def __init__(self, service: AdaptiveService | None = None) -> None:
        """Create the adaptive LangGraph wrapper around ``AdaptiveService``."""

        self.service = service or AdaptiveService()
        self.graph = self._build_graph()

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
        return builder.compile()

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
        if profile is not None:
            return {"learner_profile": profile}

        request = state.get("request")
        student_id = "anonymous"
        if request is not None:
            student_id = request.student_id or request.user_id or student_id
        return {"learner_profile": self.service.create_profile(student_id)}

    def _update_profile_node(self, state: AdaptiveWorkflowState) -> dict[str, Any]:
        """Transform graded answers into attempts and replay them into the profile.

        Args:
            state: Current adaptive workflow state.

        Returns:
            A state patch containing the updated learner profile and a compact
            audit summary of what changed.
        """

        profile = state.get("learner_profile")
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
            return {
                "profile_updates": {
                    "attempts_processed": 0,
                    "weak_topics": profile.weak_topics() if profile else [],
                    "strong_topics": profile.strong_topics() if profile else [],
                }
            }

        updated_profile, summaries = self.service.update_profile_from_attempts(
            profile,
            attempts,
        )
        return {
            "learner_profile": updated_profile,
            "profile_updates": {
                "attempts_processed": len(attempts),
                "updates": summaries,
                "weak_topics": updated_profile.weak_topics(),
                "strong_topics": updated_profile.strong_topics(),
            },
        }

    def _recommend_questions_node(self, state: AdaptiveWorkflowState) -> dict[str, Any]:
        """Score the current question bank and select the next adaptive items.

        Args:
            state: Current adaptive workflow state.

        Returns:
            A state patch containing the selected next questions.
        """

        profile = state.get("learner_profile")
        questions = [ExamQuestion.model_validate(question) for question in state.get("questions", [])]
        answers = [StudentAnswer.model_validate(answer) for answer in state.get("student_answers", [])]
        answered_question_ids = [answer.question_id for answer in answers if answer.question_id]

        if profile is None or not questions:
            return {"selected_questions": []}

        selected = self.service.select_questions(
            profile,
            questions,
            limit=min(5, len(questions)),
            exclude_question_ids=answered_question_ids,
        )
        return {"selected_questions": selected}

    def run(self, state: AdaptiveWorkflowState) -> AdaptiveWorkflowState:
        """Invoke the LangGraph adaptive workflow on a shared state dict."""

        return self.graph.invoke(state)

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
