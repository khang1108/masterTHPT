from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class Intent(str, Enum):
    ASK_HINT = "ASK_HINT"
    REVIEW_MISTAKE = "REVIEW_MISTAKE"
    VIEW_ANALYSIS = "VIEW_ANALYSIS"
    EXAM_PRACTICE = "EXAM_PRACTICE"
    PREPROCESS = "PREPROCESS"
    GRADE_SUBMISSION = "GRADE_SUBMISSION"
    UPDATE_PRACTICE = "UPDATE_PRACTICE"
    UNKNOWN = "UNKNOWN"


class ErrorType(str, Enum):
    CONCEPT_GAP = "CONCEPT_GAP"
    CALCULATION_ERROR = "CALCULATION_ERROR"
    INCOMPLETE_REASONING = "INCOMPLETE_REASONING"
    MISINTERPRETATION = "MISINTERPRETATION"
    PRESENTATION_FLAW = "PRESENTATION_FLAW"


class StudentAnswer(BaseModel):
    """Shared learner-answer payload passed between agents."""

    question_id: str
    answer: Optional[str] = None
    student_answer: Optional[str] = None
    correct_answer: Optional[str] = None
    file_urls: list[str] = Field(default_factory=list)
    time_spent_seconds: Optional[int] = None

    def normalized_answer(self) -> str:
        """Return whichever answer field is populated."""

        return (self.student_answer or self.answer or "").strip()


class ExamQuestion(BaseModel):
    """Agent-side question schema tolerant to both `id` and `question_id` inputs."""

    model_config = ConfigDict(populate_by_name=True)

    question_id: str = Field(
        validation_alias=AliasChoices("question_id", "id"),
        serialization_alias="question_id",
    )
    question_index: int = 0
    type: str = "multiple_choice"
    content: str
    content_latex: Optional[str] = None
    formulas: Optional[list[str]] = None
    options: Optional[list[str]] = None
    statements: Optional[list[str]] = None
    correct_answer: Optional[str] = None
    has_image: bool = False
    image_url: Optional[str] = None
    difficulty_a: float = 1.0
    difficulty_b: float = 0.0
    topic_tags: list[str] = Field(default_factory=list)
    max_score: float = 0.0


class ExamSection(BaseModel):
    """Logical section in an exam or practice set."""

    type: str
    section_name: str
    questions: list[ExamQuestion] = Field(default_factory=list)


class MessageRequest(BaseModel):
    """Inbound request payload exchanged between app services and agents."""

    intent: Intent | str
    student_id: Optional[str] = None
    user_id: Optional[str] = None
    exam_id: Optional[str] = None
    question_id: Optional[str] = None
    student_answers: Optional[list[StudentAnswer]] = None
    student_message: Optional[str] = None
    user_message: Optional[str] = None
    parser_output: Optional[str] = None
    content: Optional[str] = None
    file_urls: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MessageResponse(BaseModel):
    """Outbound response payload sent back to the app layer."""

    student_id: Optional[str] = None
    user_id: Optional[str] = None
    exam_id: Optional[str] = None
    question_id: Optional[str] = None
    feedback: Optional[str] = None
