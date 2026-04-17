"""Pydantic models that hold the adaptive learner state.

The adaptive service stores a compact profile rather than a large dialogue
history. This gives the selector enough signal to recommend the next questions
while staying easy to inspect during the hackathon.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class LearnerProfile(BaseModel):
    """Compact learner state used for adaptive recommendation.

    Attributes:
        student_id: Stable learner identifier.
        theta: Global ability estimate on a small IRT-like scale.
        total_attempts: Total number of graded interactions seen by the model.
        total_correct: Total number of correct interactions.
        topic_mastery: Per-topic mastery probability after BKT updates.
        topic_attempts: Per-topic attempt counts.
        topic_correct: Per-topic correct counts.
        recent_question_ids: Rolling question history used to avoid repetition.
        recent_topics: Rolling topic history used to promote diversity.
        last_updated_question_id: Most recent question that updated the profile.
    """

    student_id: str
    theta: float = 0.0
    total_attempts: int = 0
    total_correct: int = 0
    topic_mastery: dict[str, float] = Field(default_factory=dict)
    topic_attempts: dict[str, int] = Field(default_factory=dict)
    topic_correct: dict[str, int] = Field(default_factory=dict)
    recent_question_ids: list[str] = Field(default_factory=list)
    recent_topics: list[str] = Field(default_factory=list)
    last_updated_question_id: str | None = None

    def mastery_for_topic(self, topic: str, default: float = 0.25) -> float:
        """Return the current mastery estimate for a topic.

        Args:
            topic: Topic or knowledge-component identifier.
            default: Fallback mastery for unseen topics.

        Returns:
            The stored mastery value or the provided default.
        """

        return self.topic_mastery.get(topic, default)

    def accuracy(self) -> float:
        """Compute the overall observed accuracy for the learner.

        Returns:
            A value in `[0, 1]` representing total correct over total attempts.
            Unseen learners return `0.0`.
        """

        if self.total_attempts == 0:
            return 0.0
        return self.total_correct / self.total_attempts

    def weak_topics(self, threshold: float = 0.55) -> list[str]:
        """List topics whose mastery is currently below the weakness threshold.

        Args:
            threshold: Maximum mastery still considered weak.

        Returns:
            Topic identifiers sorted from weakest to strongest.
        """

        return sorted(
            [
                topic
                for topic, mastery in self.topic_mastery.items()
                if mastery < threshold
            ],
            key=lambda topic: self.topic_mastery[topic],
        )

    def strong_topics(self, threshold: float = 0.75) -> list[str]:
        """List topics whose mastery is currently above the strength threshold.

        Args:
            threshold: Minimum mastery considered strong.

        Returns:
            Topic identifiers sorted from strongest to weakest.
        """

        return sorted(
            [
                topic
                for topic, mastery in self.topic_mastery.items()
                if mastery >= threshold
            ],
            key=lambda topic: self.topic_mastery[topic],
            reverse=True,
        )
