"""Tests for manager-level autonomous orchestration across specialized agents."""

from __future__ import annotations

import pytest

from master.agents.common.learner_profile import LearnerProfile
from master.agents.common.message import (
    ExamQuestion,
    Intent,
    MessageRequest,
    MessageResponse,
    StudentAnswer,
)
from master.agents.manager.classify_intent import classify_intent, route_by_intent
from master.agents.manager.orchestrator import ManagerOrchestrator


class _FakeRepository:
    """Small async repository stub used by manager-orchestrator tests."""

    async def get_history_by_id(self, history_id: str):
        return None

    async def get_latest_history(self, *, user_id: str, exam_id: str | None = None):
        return None

    async def get_questions(
        self,
        *,
        exam_id: str | None = None,
        question_ids=None,
        topic_tags=None,
        exclude_question_ids=None,
        limit: int = 100,
    ):
        return []


class _HydrationRepository(_FakeRepository):
    """Repository stub that tracks hydration lookups and returns configured data."""

    def __init__(
        self,
        *,
        questions_by_ids=None,
        questions_by_exam=None,
    ) -> None:
        self.questions_by_ids = list(questions_by_ids or [])
        self.questions_by_exam = list(questions_by_exam or [])
        self.history_by_id_calls = 0
        self.latest_history_calls = 0
        self.question_calls: list[dict] = []

    async def get_history_by_id(self, history_id: str):
        self.history_by_id_calls += 1
        return None

    async def get_latest_history(self, *, user_id: str, exam_id: str | None = None):
        self.latest_history_calls += 1
        return None

    async def get_questions(
        self,
        *,
        exam_id: str | None = None,
        question_ids=None,
        topic_tags=None,
        exclude_question_ids=None,
        limit: int = 100,
    ):
        self.question_calls.append(
            {
                "exam_id": exam_id,
                "question_ids": list(question_ids or []),
                "topic_tags": list(topic_tags or []),
                "exclude_question_ids": list(exclude_question_ids or []),
                "limit": limit,
            }
        )
        if question_ids:
            return list(self.questions_by_ids)
        if exam_id:
            return list(self.questions_by_exam)
        return []


class _FakeAdaptiveAgent:
    """Capture the inbound state and return deterministic next questions."""

    def __init__(self) -> None:
        self.last_state = None

    def run(self, state):
        self.last_state = state
        request = state["request"]
        assert request.metadata["generate_questions"] is True
        return {
            "learner_profile": LearnerProfile(
                student_id=request.student_id or request.user_id or "anonymous",
                topic_mastery={"geometry.circle": 0.18},
                total_attempts=1,
            ),
            "selected_questions": [
                ExamQuestion(
                    question_id="next-1",
                    exam_id=request.exam_id,
                    content="Cau moi 1",
                    options=["A", "B", "C", "D"],
                    correct_answer="A",
                    topic_tags=["geometry.circle"],
                    difficulty_a=1.0,
                    difficulty_b=0.2,
                ),
                ExamQuestion(
                    question_id="next-2",
                    exam_id=request.exam_id,
                    content="Cau moi 2",
                    options=["A", "B", "C", "D"],
                    correct_answer="B",
                    topic_tags=["geometry.circle"],
                    difficulty_a=1.0,
                    difficulty_b=0.25,
                ),
            ],
            "profile_updates": {
                "attempts_processed": len(state.get("student_answers", [])),
                "weak_topics": ["geometry.circle"],
            },
        }


def test_classify_intent_prefers_request_intent() -> None:
    """Backend-provided request.intent should win over keyword heuristics."""

    state = {
        "request": MessageRequest(
            intent=Intent.VIEW_ANALYSIS,
            content="goi y cho em",
        )
    }

    classified = classify_intent(state)

    assert classified["intent"] == Intent.VIEW_ANALYSIS


def test_route_by_intent_includes_submission_and_practice_update() -> None:
    """New submission/update intents should reuse the practice router."""

    assert route_by_intent({"intent": Intent.GRADE_SUBMISSION}) == "exam_practice_router"
    assert route_by_intent({"intent": Intent.UPDATE_PRACTICE}) == "exam_practice_router"


@pytest.mark.asyncio
async def test_manager_orchestrator_runs_adaptive_then_solution_pipeline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """VIEW_ANALYSIS should trigger adaptive generation then teacher/verifier solving."""

    fake_solution_calls: list[dict] = []

    async def _fake_solution_pipeline(
        *,
        request,
        learner_profile,
        exam_id,
        questions,
        student_answers,
        max_rounds,
        confidence_threshold,
        thread_id,
    ):
        fake_solution_calls.append(
            {
                "request": request,
                "learner_profile": learner_profile,
                "exam_id": exam_id,
                "questions": questions,
                "student_answers": student_answers,
                "max_rounds": max_rounds,
                "confidence_threshold": confidence_threshold,
                "thread_id": thread_id,
            }
        )
        assert [question.question_id for question in questions] == [
            "next-1",
            "next-2",
        ]
        assert [answer.question_id for answer in student_answers] == [
            "next-1",
            "next-2",
        ]
        assert all(answer.student_answer == "" for answer in student_answers)
        return {
            "response": MessageResponse(
                student_id=request.student_id,
                exam_id=exam_id,
                feedback="Teacher + Verifier da xu ly bo cau hoi moi.",
            ),
            "debate_outputs": [
                {"question_id": "next-1"},
                {"question_id": "next-2"},
            ],
        }

    monkeypatch.setattr(
        "master.agents.manager.orchestrator._run_teacher_verifier_solution_pipeline",
        _fake_solution_pipeline,
    )

    adaptive_agent = _FakeAdaptiveAgent()
    orchestrator = ManagerOrchestrator(
        repository=_FakeRepository(),
        adaptive_agent=adaptive_agent,
    )

    final_state = await orchestrator.run(
        {
            "request": MessageRequest(
                intent=Intent.VIEW_ANALYSIS,
                user_id="user-42",
                exam_id="exam-42",
            ),
            "questions": [
                ExamQuestion(
                    question_id="done-1",
                    exam_id="exam-42",
                    content="Cau da lam",
                    options=["A", "B", "C", "D"],
                    correct_answer="A",
                    topic_tags=["geometry.circle"],
                )
            ],
            "student_answers": [
                StudentAnswer(
                    question_id="done-1",
                    student_answer="B",
                )
            ],
            "_thread_id": "manager-test-42",
        }
    )

    response = final_state["response"]
    payload = response.model_dump(mode="json")

    assert adaptive_agent.last_state is not None
    assert adaptive_agent.last_state["request"].student_id == "user-42"
    assert adaptive_agent.last_state["request"].metadata["generate_questions"] is True
    assert fake_solution_calls
    assert payload["feedback"] == "Teacher + Verifier da xu ly bo cau hoi moi."
    assert [question["question_id"] for question in payload["selected_questions"]] == [
        "next-1",
        "next-2",
    ]
    assert payload["profile_updates"]["attempts_processed"] == 1
    assert payload["agent_trail"] == ["manager", "adaptive", "teacher", "verifier"]


@pytest.mark.asyncio
async def test_hydrate_uses_legacy_student_ans_payload_without_history_lookup() -> None:
    """Legacy ``student_ans`` list payload should hydrate without DB history round-trips."""

    repository = _HydrationRepository(
        questions_by_ids=[
            {
                "id": "q-legacy-1",
                "exam_id": "exam-legacy",
                "content": "Cau hoi legacy",
                "options": ["A", "B", "C", "D"],
                "correct_answer": "A",
                "topic_tags": ["algebra.linear"],
            }
        ]
    )
    orchestrator = ManagerOrchestrator(
        repository=repository,
        adaptive_agent=_FakeAdaptiveAgent(),
    )

    request = MessageRequest(
        intent=Intent.GRADE_SUBMISSION,
        user_id="user-legacy",
        exam_id="exam-legacy",
        student_ans=[
            {
                "question_id": "q-legacy-1",
                "student_answer": "A",
            }
        ],
    )

    hydrated = await orchestrator._hydrate_backend_context_node(
        {
            "request": request,
            "intent": Intent.GRADE_SUBMISSION,
        }
    )

    answers = hydrated["student_answers"]
    questions = hydrated["questions"]

    assert [answer.question_id for answer in answers] == ["q-legacy-1"]
    assert [answer.student_answer for answer in answers] == ["A"]
    assert [question.question_id for question in questions] == ["q-legacy-1"]
    assert repository.history_by_id_calls == 0
    assert repository.latest_history_calls == 0


@pytest.mark.asyncio
async def test_hydrate_falls_back_to_exam_lookup_when_answer_ids_miss() -> None:
    """Hydration should fetch by exam when answer-based question lookup returns nothing."""

    repository = _HydrationRepository(
        questions_by_ids=[],
        questions_by_exam=[
            {
                "id": "exam-fallback-1",
                "exam_id": "exam-fallback",
                "content": "Cau hoi fallback",
                "options": ["A", "B", "C", "D"],
                "correct_answer": "B",
                "topic_tags": ["geometry.circle"],
            }
        ],
    )
    orchestrator = ManagerOrchestrator(
        repository=repository,
        adaptive_agent=_FakeAdaptiveAgent(),
    )

    request = MessageRequest(
        intent=Intent.VIEW_ANALYSIS,
        user_id="user-fallback",
        exam_id="exam-fallback",
    )

    hydrated = await orchestrator._hydrate_backend_context_node(
        {
            "request": request,
            "intent": Intent.VIEW_ANALYSIS,
            "history_record": {
                "_id": "507f1f77bcf86cd799439011",
                "student_ans": [
                    {
                        "question_id": "missing-question-id",
                        "student_answer": "C",
                    }
                ],
            },
        }
    )

    assert len(repository.question_calls) == 2
    assert repository.question_calls[0]["question_ids"] == ["missing-question-id"]
    assert repository.question_calls[0]["exam_id"] is None
    assert repository.question_calls[1]["exam_id"] == "exam-fallback"
    assert [question.question_id for question in hydrated["questions"]] == ["exam-fallback-1"]
