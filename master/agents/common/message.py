from __future__ import annotations # For type hints in Python 3.10+

from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field

import uuid

class Intent(str, Enum):
    EXAM_PRACTICE = "EXAM_PRACTICE"
    GRADE_SUBMISSION = "GRADE_SUBMISSION"
    VIEW_ANALYSIS = "VIEW_ANALYSIS"
    ASK_HINT = "ASK_HINT"
    REVIEW_MISTAKE = "REVIEW_MISTAKE"
    UNKNOWN = "UNKNOWN"

class ErrorType(str, Enum):
    CONCEPT_GAP = "CONCEPT_GAP"
    CALCULATION_ERROR = "CALCULATION_ERROR"
    INCOMPLETE_REASONING = "INCOMPLETE_REASONING"
    MISINTERPRETATION = "MISINTERPRETATION"
    PRESENTATION_FLAW = "PRESENTATION_FLAW"


"""
Message for NestJS <-> Agent Service communication.

INTENT = "EXAM_PRACTICE"
    - Metadata:
        + subject: str
        + total_questions: int
        + exam_sections: list[ExamSection]
INTENT = "GRADE_SUBMISSION"
    - Metadata:
        + file_urls: list[str]

INTENT = "VIEW_ANALYSIS"
    - Metadata:
        + exam_id: str
        + student_id: str
        + session_id: str
        + total_questions: int
        + exam_sections: list[ExamSection]
        + student_answers: list[StudentAnswer]
INTENT = "ASK_HINT"
    - Metadata:
        + question_id: str
        + exam_id: str
INTENT = "REVIEW_MISTAKE"
    - Metadata:
        + exam_id: str
        + questions: list[ExamQuestion]
INTENT = "UNKNOWN"
    - Metadata:
        + context: str
"""
class MessageRequest(BaseModel):
    student_id: str
    session_id: Optional[str] = None
    intent: Intent
    user_message: str
    file_urls: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MessageResponse(BaseModel):
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: str  # "success" | "error"
    intent: Intent
    result: dict[str, Any] = Field(default_factory=dict)
    agent_trail: list[str] = Field(default_factory=list)
    error_message: Optional[str] = None


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
    question_index: int 
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
    type: str # ["multiple_choice", "essay", ...]
    questions: list[ExamQuestion]


class ExamData(BaseModel):
    exam_id: str
    source: str  # "image" | "pdf" | "manual"
    subject: str
    exam_type: str
    total_questions: int
    sections: list[ExamSection]
    duration_minutes: Optional[int] = None


# --- Evaluation JSON Schema ---

class ErrorAnalysis(BaseModel):
    error_type: ErrorType
    root_cause: str
    knowledge_component: str
    remedial: str


class StudentAnswer(BaseModel):
    exam_id: str
    question_id: str
    answer: Optional[str] = None
    correct_answer: Optional[str] = None
    file_urls: list[str] = Field(default_factory=list)


class OverallAnalysis(BaseModel):
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    recommended_topics: list[str] = Field(default_factory=list)
