from __future__ import annotations # For type hints in Python 3.10+

from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field, model_validator

import uuid

class Intent(str, Enum):
    ASK_HINT = "ASK_HINT"
    REVIEW_MISTAKE = "REVIEW_MISTAKE"
    VIEW_ANALYSIS = "VIEW_ANALYSIS"
    EXAM_PRACTICE = "EXAM_PRACTICE"
    PREPROCESS = "PREPROCESS"
    GRADE_SUBMISSION = "GRADE_SUBMISSION"
    UNKNOWN = "UNKNOWN"

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

INTENT = PREPROCES
    - Metadata:
        + parser_output
"""


class MessageRequest(BaseModel):
    intent: Intent
    student_id: str
    exam_id: Optional[str] = None
    question_id: Optional[str] = None
    student_answers: Optional[list["StudentAnswer"]] = None
    student_message: Optional[str] = None
    user_message: Optional[str] = None
    parser_output: Optional[str] = None
    content: Optional[str] = None
    metadata: Optional[dict] = None
    file_urls: Optional[list[str]] = None

class MessageResponse(BaseModel):
    student_id: str
    exam_id: Optional[str] = None
    question_id: Optional[str] = None
    feedback: Optional[str] = None

# --- Exam JSON Schema ---

class ExamQuestion(BaseModel):
    """
    A multiple-choice question in an exam.

    Args:
        id: The id of the question
        question_index: The index of the question in the section
        content: The content of the question
        content_latex: The LaTeX content of the question
        options: The options of the question
        correct_answer: The correct answer of the question
        has_image: Whether the question has an image
        image_url: The URL of the image
        difficulty_a: The difficulty of the question
        difficulty_b: The difficulty of the question
        topic_tags: The topic tags of the question
        max_score: The maximum score of the question
    """
    question_id: str
    type: str  # "multiple_choice" | "essay"
    content: str
    formulas: Optional[list[str]] = None # LaTeX formulas in the question
    options: Optional[list[str]] = None
    correct_answer: Optional[str] = None
    has_image: bool = False
    image_url: Optional[str] = None
    difficulty_a: float = 1.0
    difficulty_b: float = 0.0
    topic_tags: list[str] = Field(default_factory=list) # ["math.12.ch2.integrals", "math.12.ch4.solid_geometry", ...]
    max_score: float = 0.2

class ExamSection(BaseModel):
    """A section of an exam grouping questions of the same type."""
    type: str  # "multiple_choice" | "essay"
    questions: list[ExamQuestion] = Field(default_factory=list)


# --- Evaluation JSON Schema ---

class ErrorAnalysis(BaseModel):
    error_type: ErrorType
    root_cause: str
    knowledge_component: str
    remedial: str


class StudentAnswer(BaseModel):
    question_id: str
    exam_id: Optional[str] = None
    answer: Optional[str] = None           # Student's answer (primary field)
    student_answer: Optional[str] = None   # Deprecated alias — use `answer` instead
    correct_answer: Optional[str] = None
    file_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _sync_answer_fields(self) -> "StudentAnswer":
        """Keep `answer` and `student_answer` in sync for backward compatibility."""
        if self.answer is None and self.student_answer is not None:
            self.answer = self.student_answer
        elif self.student_answer is None and self.answer is not None:
            self.student_answer = self.answer
        return self


# Resolve forward reference in MessageRequest
MessageRequest.model_rebuild()


class OverallAnalysis(BaseModel):
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    recommended_topics: list[str] = Field(default_factory=list)
