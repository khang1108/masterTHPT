"""Typed recommendation objects returned by the adaptive selector."""

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
