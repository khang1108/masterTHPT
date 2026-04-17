"""Typed outputs used by adaptive selection and adaptive question generation."""

from __future__ import annotations

from pydantic import BaseModel, Field


class QuestionRecommendation(BaseModel):
    """One ranked question recommendation produced by the adaptive service.

    The object is intentionally explanation-friendly: besides the final score it
    carries the target topic, prerequisite context, and short textual reasons
    that can be surfaced in logs or UI.
    """

    question_id: str
    score: float
    target_topic: str | None = None
    target_label: str | None = None
    estimated_correct_probability: float
    topic_tags: list[str] = Field(default_factory=list)
    prerequisite_topics: list[str] = Field(default_factory=list)
    prerequisite_labels: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)


class GeneratedQuestionDraft(BaseModel):
    """Structured draft of one new question produced from RAG context."""

    content: str
    content_latex: str | None = None
    options: list[str] = Field(default_factory=list)
    correct_answer: str
    topic_tags: list[str] = Field(default_factory=list)
    difficulty_a: float = 1.0
    difficulty_b: float = 0.0
    type: str = "multiple_choice"
    max_score: float | None = 1.0


class GeneratedQuestionBatch(BaseModel):
    """Structured output batch for adaptive question generation."""

    questions: list[GeneratedQuestionDraft] = Field(default_factory=list)
