from __future__ import annotations # For type hints in Python 3.10+

from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field

class Intent(str, Enum):
    ASK_HINT = "ASK_HINT"
    REVIEW_MISTAKE = "REVIEW_MISTAKE"
    VIEW_ANALYSIS = "VIEW_ANALYSIS"
    EXAM_PRACTICE = "EXAM_PRACTICE"
    PREPROCESS = "PREPROCESS"

class ErrorType(str, Enum):
    CONCEPT_GAP = "CONCEPT_GAP"
    CALCULATION_ERROR = "CALCULATION_ERROR"
    INCOMPLETE_REASONING = "INCOMPLETE_REASONING"
    MISINTERPRETATION = "MISINTERPRETATION"
    PRESENTATION_FLAW = "PRESENTATION_FLAW"


"""
Message for NestJS <-> Agent Service communication.

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

INTENT = PREPROCESS
    - Metadata:
        + parser_output: list[dict]
"""


class MessageRequest(BaseModel):
    intent: Intent
    student_id: str
    exam_id: Optional[str] = None
    question_id: Optional[str] = None
    student_answers: Optional[list[StudentAnswer]] = None
    student_message: Optional[str] = None
    parser_output: Optional[list[dict]] = None
    image_bucket_url: Optional[str] = None

class MessageResponse(BaseModel):
    student_id: str
    exam_id: Optional[str] = None
    question_id: Optional[str] = None
    feedback: Optional[str] = None

# --- Exam JSON Schema ---

class ExamQuestion(BaseModel):
    id: Optional[str] = None
    question_index: Optional[int] = None
    type: str = "multiple_choice"  # "multiple_choice" | "essay"
    content: str = ""
    content_latex: Optional[str] = None
    options: list[str] = Field(default_factory=list)
    correct_answer: Optional[str] = None
    has_image: bool = False
    image_url: Optional[str] = None
    difficulty_a: float = 1.0
    difficulty_b: float = 0.0
    topic_tags: list[str] = Field(default_factory=list)
    max_score: Optional[float] = None


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

class OverallAnalysis(BaseModel):
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    recommended_topics: list[str] = Field(default_factory=list)
