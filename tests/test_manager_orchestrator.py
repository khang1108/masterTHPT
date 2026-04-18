"""Tests for manager-level autonomous orchestration across specialized agents."""

from __future__ import annotations

import pytest

from master.agents.common.execution_plan import ExecutionAgent, FinalResponseMode
from master.agents.common.learner_profile import LearnerProfile
from master.agents.common.message import (
    ExamQuestion,
    Intent,
    MessageRequest,
    StudentAnswer,
)
from master.agents.common.tools import ToolsRegistry
from master.agents.manager.classify_intent import classify_intent, route_by_intent
from master.agents.manager.orchestrator import ManagerOrchestrator
from master.agents.manager.request_planner import RequestPlannerAgent


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
async def test_manager_orchestrator_runs_request_planner_then_adaptive() -> None:
    """VIEW_ANALYSIS should go through planner, then the adaptive specialist step."""

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
    assert payload["feedback"] == "Adaptive đã phân tích lịch sử làm bài và cập nhật hồ sơ học tập."
    assert [question["question_id"] for question in payload["selected_questions"]] == [
        "next-1",
        "next-2",
    ]
    assert payload["profile_updates"]["attempts_processed"] == 1
    assert payload["agent_trail"] == ["manager", "adaptive"]
    assert payload["planner_summary"].startswith("Planner chọn workflow VIEW_ANALYSIS")
    assert payload["step_results"][0]["agent"] == "adaptive"
    assert payload["tool_trace"][0]["agent"] == "adaptive"


def test_request_planner_routes_hint_to_teacher_only() -> None:
    """Hint requests should produce a one-step teacher plan with hint response mode."""

    planner = RequestPlannerAgent()
    plan, summary = planner.build_plan(
        {
            "intent": Intent.ASK_HINT,
            "request": MessageRequest(intent=Intent.ASK_HINT, student_id="student-1"),
        }
    )

    assert plan is not None
    assert plan.final_response_mode == FinalResponseMode.HINT
    assert [step.agent for step in plan.steps] == [ExecutionAgent.TEACHER]
    assert "ASK_HINT" in summary


def test_request_planner_routes_review_to_teacher_then_verifier() -> None:
    """Review requests should explicitly plan teacher followed by verifier."""

    planner = RequestPlannerAgent()
    plan, _ = planner.build_plan(
        {
            "intent": Intent.REVIEW_MISTAKE,
            "request": MessageRequest(intent=Intent.REVIEW_MISTAKE, student_id="student-1"),
        }
    )

    assert plan is not None
    assert plan.requires_verification is True
    assert [step.agent for step in plan.steps] == [
        ExecutionAgent.TEACHER,
        ExecutionAgent.VERIFIER,
    ]


def test_tool_scoping_exposes_role_specific_bundle_names() -> None:
    """Scoped tool policy should keep specialist visibility narrow and explicit."""

    teacher_tools = ToolsRegistry.get_tool_names_for_role("teacher")
    verifier_tools = ToolsRegistry.get_tool_names_for_role("verifier")
    adaptive_tools = ToolsRegistry.get_tool_names_for_role("adaptive")
    parser_tools = ToolsRegistry.get_tool_names_for_role("parser")

    assert "python_repl" in teacher_tools
    assert "trace_knowledge_graph_topics" in teacher_tools
    assert teacher_tools == verifier_tools
    assert adaptive_tools == []
    assert "read_file" in parser_tools
    assert "python_repl" not in parser_tools


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
