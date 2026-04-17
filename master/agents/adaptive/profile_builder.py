"""Helpers for adaptive learner-profile updates and attempt normalization."""

from __future__ import annotations

from typing import Iterable

from pydantic import BaseModel, Field

from master.agents.common.learner_profile import LearnerProfile
from master.agents.common.message import ExamQuestion


def _dedupe_preserve_order(values: Iterable[str]) -> list[str]:
    """Remove duplicates from an iterable while preserving encounter order."""

    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


class AdaptiveAttempt(BaseModel):
    """Normalized graded interaction used to update the learner profile."""

    question_id: str
    is_correct: bool
    topic_tags: list[str] = Field(default_factory=list)
    knowledge_components: list[str] = Field(default_factory=list)
    difficulty_b: float = 0.0
    discrimination_a: float = 1.0

    def covered_topics(self) -> list[str]:
        """Return the unique list of topic signals associated with this attempt."""

        return _dedupe_preserve_order([*self.knowledge_components, *self.topic_tags])

    @classmethod
    def from_question(
        cls,
        question: ExamQuestion,
        *,
        is_correct: bool,
    ) -> "AdaptiveAttempt":
        """Create a normalized attempt from an exam-question record."""

        return cls(
            question_id=question.question_id,
            is_correct=is_correct,
            topic_tags=list(question.topic_tags),
            difficulty_b=question.difficulty_b,
            discrimination_a=question.difficulty_a,
        )


def create_profile(
    student_id: str,
    *,
    initial_theta: float = 0.0,
    initial_mastery: dict[str, float] | None = None,
) -> LearnerProfile:
    """Create a fresh learner profile ready for adaptive recommendation.

    Args:
        student_id: Stable learner identifier.
        initial_theta: Optional starting global ability estimate.
        initial_mastery: Optional seeded topic mastery map.

    Returns:
        A newly initialized learner profile.
    """

    return LearnerProfile(
        student_id=student_id,
        theta=initial_theta,
        topic_mastery=dict(initial_mastery or {}),
    )


def push_recent_history(
    profile: LearnerProfile,
    *,
    question_id: str,
    topics: Iterable[str],
    limit: int = 20,
) -> None:
    """Append a new interaction to the rolling history windows.

    Args:
        profile: Learner profile being updated in place.
        question_id: Newly completed question id.
        topics: Topics touched by the latest attempt.
        limit: Maximum rolling window size for recent history lists.
    """

    profile.recent_question_ids = [
        *profile.recent_question_ids[-(limit - 1):],
        question_id,
    ]
    merged_topics = [*profile.recent_topics, *_dedupe_preserve_order(topics)]
    profile.recent_topics = merged_topics[-limit:]
    profile.last_updated_question_id = question_id
