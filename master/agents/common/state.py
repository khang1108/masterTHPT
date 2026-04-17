"""Shared LangGraph state definition for the grading pipeline.

The runtime pipeline uses plain dictionaries, but this ``TypedDict`` keeps the
expected keys visible to maintainers and type checkers. The graph evolves over
time, so the state is declared with ``total=False`` to allow partially-built
states during intermediate steps.
"""

from __future__ import annotations

from typing import Any, Literal, TypedDict

from master.agents.common.learner_profile import LearnerProfile
from master.agents.common.message import (
    ExamQuestion,
    Intent,
    MessageRequest,
    MessageResponse,
    StudentAnswer,
)
from master.common.message import GradeResult, Solution


class AgentState(TypedDict, total=False):
    """Top-level mutable state passed through the grading graph."""

    request: MessageRequest | None
    raw_request: MessageRequest | None
    intent: Intent

    learner_profile: LearnerProfile | None

    exam_id: str | None
    questions: list[ExamQuestion]
    student_answers: list[StudentAnswer]

    round: int
    max_round: int
    phase: Literal["draft", "debate", "verify", "finalize"]
    debate_outputs: list[Any]

    grade_result: GradeResult | None
    solutions: list[Solution] | None
    verified_solutions: list[Solution] | None

    selected_questions: list[ExamQuestion] | None
    profile_updates: dict[str, Any] | None

    response: MessageResponse | None
    agent_trail: list[str] | None
    history_record: dict[str, Any] | None

    _verdicts: list[Any]
    _pipeline_verdict: str
    _teacher_confidence_threshold: float
    _thread_id: str
    _start_phase: str
    _file_path: str
    _student_id: str
    _parser_batch_size: int | None
    _stop_pipeline: bool
