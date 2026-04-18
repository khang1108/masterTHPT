"""Shared LangGraph state definition for the grading and adaptive pipeline."""

from __future__ import annotations

from typing import Any, Literal, TypedDict

from master.agents.common.execution_plan import ExecutionPlan, StepResult
from master.agents.common.learner_profile import LearnerProfile
from master.agents.common.message import (
    ExamQuestion,
    Intent,
    MessageRequest,
    MessageResponse,
    StudentAnswer,
)
from master.agents.common.shared_plan_memory import SharedPlanMemory
from master.common.message import GradeResult


class AgentState(TypedDict, total=False):
    """Top-level mutable state passed through the orchestration graph."""

    request: MessageRequest | None
    raw_request: MessageRequest | None
    intent: Intent | str

    learner_profile: LearnerProfile | None
    active_plan: SharedPlanMemory | None
    execution_plan: ExecutionPlan | None

    exam_id: str | None
    questions: list[ExamQuestion]
    student_answers: list[StudentAnswer]

    round: int
    max_round: int
    is_agreed: list[bool]
    phase: Literal["tools", "draft", "debate", "verify", "finalize", "END"]
    is_agreed: List[bool]
    reasoning: str
    confidence: list[float]
    teacher_feedback: list[Any]
    verifier_feedback: list[Any]

    grade_result: GradeResult | None

    selected_questions: list[ExamQuestion] | None
    profile_updates: dict[str, Any] | None
    plan_patch: dict[str, Any] | None
    plan_proposal: dict[str, Any] | None
    step_results: list[StepResult] | None
    planner_summary: str | None
    tool_trace: list[dict[str, Any]] | None
    allowed_tools: list[str] | None
    needs_replan: bool
    replan_count: int

    response: MessageResponse | None
    agent_trail: list[str] | None
    history_record: dict[str, Any] | None

    discrimination_a: list[float] | None
    difficulty_b: list[float] | None
    topic_tags: list[list[str]] | None

    debate_outputs: list[Any]
    _verdicts: list[Any]
    _pipeline_verdict: str
    _teacher_confidence_threshold: float
    _thread_id: str
    _start_phase: str
    _file_path: str
    _student_id: str
    _parser_batch_size: int | None
    _stop_pipeline: bool
