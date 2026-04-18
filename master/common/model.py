from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field
from master.agents.common.message import Intent, ErrorType

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
    student_answers: Optional[list[StudentAnswer]] = None
    student_message: Optional[str] = None
    parser_output: Optional[str] = None
    content: Optional[str] = None # Nội dung thêm, nếu cần thiết.

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
        discrimination_a: The discrimination of the question
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
    discrimination_a: float = 1.0
    difficulty_b: float = 0.0
    topic_tags: list[str] = Field(default_factory=list) # ["math.12.ch2.integrals", "math.12.ch4.solid_geometry", ...]
    max_score: float = 0.2

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
