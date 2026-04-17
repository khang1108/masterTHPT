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

"""
INTENT = "ASK_HINT"
    - Metadata:
        + student_id: str
        + questions_id: str

INTENT = "REVIEW_MISTAKE"
    - Metadata:
        + student_id: str
        + question_id: str
        + student_answers: list[StudentAnswer]

INTENT = "VIEW_ANALYSIS"
    - Metadata:
        + student_id: str
        + exam_id: str
        + student_answers: list[StudentAnswer]

INTENT = "EXAM_PRACTICE"
    - Metadata:
        + student_id: str
        + exam_id: str
        + student_answers: list[StudentAnswer]

INTENT = PREPROCES
    - Metadata:
        + parser_output
"""


class MessageRequest(BaseModel):
    intent: Intent
    student_id: str
    exam_id: Optional[str] = None
    question_id: Optional[str] = None
    student_answers: Optional[list[StudentAnswer]] = None
    student_message: Optional[str] = None
    parser_output: Optional[str] = None
    image_bucket_url: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    file_urls: list[str] = Field(default_factory=list)

class MessageResponse(BaseModel):
    student_id: str
    exam_id: Optional[str] = None
    question_id: Optional[str] = None
    feedback: Optional[str] = None
    preprocess_payload: Optional[PreprocessPayload] = None

class ExamQuestion(BaseModel):
    """Agent-side question schema tolerant to both `id` and `question_id` inputs."""

    model_config = ConfigDict(populate_by_name=True)

    question_id: str = Field(
        validation_alias=AliasChoices("question_id", "id"),
        serialization_alias="question_id",
    )
    content: str
    content_latex: Optional[str] = None
    options: Optional[list[str]] = None
    exam_id: Optional[str] = None
    type: str = "multiple_choice"  # "multiple_choice" | "essay"
    correct_answer: Optional[str] = None
    has_image: bool = False
    image_url: Optional[str] = None
    difficulty_a: float = 1.0
    difficulty_b: float = 0.0
    topic_tags: list[str] = Field(default_factory=list)
    max_score: float = 0.0

class ExamDocument(BaseModel):
    id: Optional[str] = None
    subject: str = "Toán"
    exam_type: str = "PREPROCESS_OCR"
    grade: int = 12
    year: int
    source: str = "OCR_PARSER"
    generated: bool = False
    total_questions: int = 0
    duration: int = 90
    metadata: Optional[dict[str, Any]] = None
    created_at: Optional[str] = None
    questions: list[str] = Field(default_factory=list)

class PreprocessPayload(BaseModel):
    exam: ExamDocument
    questions: list[ExamQuestion] = Field(default_factory=list)

# --- Evaluation JSON Schema ---

class ErrorAnalysis(BaseModel):
    error_type: ErrorType
    root_cause: str
    knowledge_component: str
    remedial: str


class StudentAnswer(BaseModel):
    question_id: str
    student_answer: Optional[str] = None

class MessageResponse(BaseModel):
    """Outbound response payload sent back to the app layer."""

    student_id: Optional[str] = None
    user_id: Optional[str] = None
    exam_id: Optional[str] = None
    question_id: Optional[str] = None
    feedback: Optional[str] = None
