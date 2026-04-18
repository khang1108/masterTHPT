"""Shared message and exam-domain schemas used across the agent pipeline.

These models sit at the boundary between parser, teacher, verifier, adaptive,
and the external application layer. The codebase still contains a few legacy
payload shapes, so the models intentionally accept compatible aliases:

- ``id`` and ``question_id`` for exam questions
- ``answer`` and ``student_answer`` for learner responses
- ``content`` / ``student_message`` / ``user_message`` for free-form text
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator, model_validator


class Intent(str, Enum):
    """Top-level request intent routed by the orchestration layer."""

    ASK_HINT = "ASK_HINT"
    REVIEW_MISTAKE = "REVIEW_MISTAKE"
    VIEW_ANALYSIS = "VIEW_ANALYSIS"
    EXAM_PRACTICE = "EXAM_PRACTICE"
    GRADE_SUBMISSION = "GRADE_SUBMISSION"
    PREPROCESS = "PREPROCESS"
    UPDATE_PRACTICE = "UPDATE_PRACTICE"
    UNKNOWN = "UNKNOWN"


class ErrorType(str, Enum):
    """Normalized error categories emitted by evaluation flows."""

    CONCEPT_GAP = "CONCEPT_GAP"
    CALCULATION_ERROR = "CALCULATION_ERROR"
    INCOMPLETE_REASONING = "INCOMPLETE_REASONING"
    MISINTERPRETATION = "MISINTERPRETATION"
    PRESENTATION_FLAW = "PRESENTATION_FLAW"


class StudentAnswer(BaseModel):
    """Learner response payload shared between grading and adaptive flows."""

    model_config = ConfigDict(extra="allow")

    question_id: str
    answer: str | None = None
    student_answer: str | None = None
    correct_answer: str | None = None
    file_urls: list[str] = Field(default_factory=list)
    time_spent_seconds: int | None = None

    @model_validator(mode="after")
    def _sync_answer_fields(self) -> "StudentAnswer":
        """Mirror legacy answer fields so downstream code can use either one."""

        if self.student_answer is None and self.answer is not None:
            self.student_answer = self.answer
        if self.answer is None and self.student_answer is not None:
            self.answer = self.student_answer
        return self

    def normalized_answer(self) -> str:
        """Canonical normalized answer string used for grading and analysis."""

        return (self.student_answer or "").strip().lower()
"""
INTENT = PREPROCESS
    - Metadata:
        + parser_output: list[dict]
"""

class MessageRequest(BaseModel):
    intent: Intent
    student_id: str
    exam_id: Optional[str] = None
    question_id: Optional[str] = None
    student_answers: Optional[StudentAnswer] = None
    student_message: Optional[str] = None
    parser_output: Optional[list[dict]] = None
    image_bucket_url: Optional[str] = None
    file_path: Optional[str] = None

class MessageResponse(BaseModel):
    student_id: str
    exam_id: Optional[str] = None
    question_id: Optional[str] = None
    feedback: Optional[str] = None

# --- Exam JSON Schema ---

class ExamQuestion(BaseModel):
    """Normalized exam-question schema tolerant to legacy aliases."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    question_id: str = Field(
        validation_alias=AliasChoices("question_id", "id"),
        serialization_alias="question_id",
    )
    exam_id: str | None = None
    question_index: int = 0
    type: str = "multiple_choice"
    content: str = ""
    content_latex: str | None = None
    options: list[str] = Field(default_factory=list)
    correct_answer: str | None = None
    has_image: bool = False
    image_url: str | None = None
    # Keep ``discrimination_a`` as the canonical field name, but still accept
    # the historical misspelling ``discrimnination_a`` from older documents.
    discrimination_a: float = Field(
        default=1.0,
        validation_alias=AliasChoices("discrimination_a", "discrimnination_a"),
        serialization_alias="discrimination_a",
    )
    difficulty_b: float = 0.0
    topic_tags: list[str] = Field(default_factory=list)
    max_score: float | None = None

    @field_validator("options", "topic_tags", mode="before")
    @classmethod
    def _coerce_list_fields(cls, value: Any) -> list[str]:
        """Normalize nullable/legacy list payloads from DB and APIs.

        Some historical records store list-like fields as ``null`` or plain
        strings. We coerce these into stable string lists so validation remains
        tolerant without leaking ``None`` into the agent pipeline.
        """

        if value is None:
            return []
        if isinstance(value, (list, tuple, set)):
            return [str(item) for item in value if item is not None]
        if isinstance(value, str):
            stripped = value.strip()
            return [stripped] if stripped else []
        return [str(value)]

    @property
    def id(self) -> str:
        """Backward-compatible accessor used by older pipeline code."""

        return self.question_id

    @property
    def discrimnination_a(self) -> float:
        """Backward-compatible accessor for legacy typo-based callers."""

        return self.discrimination_a


class ExamSection(BaseModel):
    """Logical section within an exam document or extracted practice set."""

    model_config = ConfigDict(extra="allow")

    type: str = ""
    section_name: str = ""
    questions: list[ExamQuestion] = Field(default_factory=list)


class ExamDocument(BaseModel):
    """Metadata persisted for an extracted or generated exam."""

    model_config = ConfigDict(extra="allow")

    id: str | None = None
    subject: str = "Toán"
    exam_type: str = "PREPROCESS_OCR"
    grade: int | None = 12
    year: int | None = None
    source: str = "OCR_PARSER"
    generated: bool = False
    total_questions: int = 0
    duration: int = 90
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str | None = None
    questions: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _sync_total_questions(self) -> "ExamDocument":
        """Default total question count from the embedded question-id list."""

        if not self.total_questions and self.questions:
            self.total_questions = len(self.questions)
        return self


class PreprocessPayload(BaseModel):
    """Structured preprocess result used by OCR/parser and debate stages."""

    model_config = ConfigDict(extra="allow")

    exam: ExamDocument
    questions: list[ExamQuestion] = Field(default_factory=list)


class ErrorAnalysis(BaseModel):
    """Structured description of why a learner response failed."""

    model_config = ConfigDict(extra="allow")

    error_type: ErrorType
    root_cause: str
    knowledge_component: str
    remedial: str


class MessageRequest(BaseModel):
    """Inbound request payload exchanged between services and agents."""

    model_config = ConfigDict(extra="allow")

    intent: Intent | str
    student_id: str | None = None
    user_id: str | None = None
    exam_id: str | None = None
    question_id: str | None = None
    student_answers: list[StudentAnswer] | None = None
    student_message: str | None = None
    user_message: str | None = None
    parser_output: str | None = None
    content: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    file_urls: list[str] = Field(default_factory=list)
    image_bucket_url: str | None = None

    @field_validator("student_answers", mode="before")
    @classmethod
    def _coerce_student_answers(cls, value: Any) -> Any:
        """Accept either a single student-answer object or a list of them."""

        if value is None:
            return None
        if isinstance(value, dict):
            return [value]
        return value

    @model_validator(mode="after")
    def _sync_message_fields(self) -> "MessageRequest":
        """Populate text aliases so intent classification has one stable field."""

        if not self.content:
            self.content = self.user_message or self.student_message or ""
        if self.student_message is None and self.content:
            self.student_message = self.content
        if self.user_message is None and self.content:
            self.user_message = self.content
        return self


class MessageResponse(BaseModel):
    """Outbound response payload returned by the agent orchestration layer."""

    model_config = ConfigDict(extra="allow")

    student_id: str | None = None
    user_id: str | None = None
    exam_id: str | None = None
    question_id: str | None = None
    feedback: str | None = None
    preprocess_payload: PreprocessPayload | None = None
