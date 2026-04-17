"""Simple CAT-style scoring heuristics for adaptive question selection."""

from __future__ import annotations

from statistics import mean
from typing import Iterable, Sequence
from pydantic import BaseModel
from master.agents.common.learner_profile import LearnerProfile

from .ability import expected_correct_probability
from .graph import AdaptiveGraph


class RecommendationWeights(BaseModel):
    """Heuristic weights for the adaptive ranking function."""

    priority_match: float = 0.30
    weakness_alignment: float = 0.20
    difficulty_match: float = 0.20
    novelty: float = 0.15
    prerequisite_readiness: float = 0.10
    topic_coverage: float = 0.05


def _mean_or_default(values: Sequence[float], default: float) -> float:
    """Return the arithmetic mean or a fallback when the input is empty."""

    return mean(values) if values else default


def difficulty_match_score(
    *,
    theta: float,
    difficulty: float,
    discrimination: float,
    target_probability: float = 0.68,
) -> tuple[float, float]:
    """Estimate success probability and score closeness to a productive target band.

    Args:
        theta: Current global ability estimate of the learner.
        difficulty: Difficulty value attached to the candidate question.
        discrimination: Item discrimination used by the IRT-like curve.
        target_probability: Desired success zone for productive practice.

    Returns:
        A tuple ``(estimated_probability, match_score)`` where the score is
        highest when the predicted success probability sits near the target band.
    """

    probability = expected_correct_probability(
        theta=theta,
        difficulty=difficulty,
        discrimination=discrimination,
    )
    score = max(0.0, 1.0 - abs(probability - target_probability) / target_probability)
    return probability, score


def weakness_alignment_score(
    *,
    topics: Sequence[str],
    profile: LearnerProfile,
) -> float:
    """Prefer questions on topics whose mastery is still low.

    Args:
        topics: Candidate topic ids associated with a question.
        profile: Current learner profile.

    Returns:
        Mean knowledge gap over the covered topics, where larger values mean the
        question aligns more strongly with weak areas.
    """

    gaps = [1.0 - profile.mastery_for_topic(topic) for topic in topics]
    return _mean_or_default(gaps, default=0.40)


def novelty_score(
    *,
    question_id: str,
    topics: Sequence[str],
    profile: LearnerProfile,
) -> float:
    """Penalize immediate repetition of questions or recently drilled topics.

    Args:
        question_id: Candidate question identifier.
        topics: Candidate topics attached to that question.
        profile: Current learner profile.

    Returns:
        A novelty score in ``[0, 1]`` where higher means less repetition with
        the recent interaction history.
    """

    score = 1.0
    if question_id in profile.recent_question_ids:
        score -= 0.55
    repeated_topics = sum(1 for topic in topics if topic in profile.recent_topics)
    score -= min(0.40, repeated_topics * 0.15)
    return max(0.0, score)


def prerequisite_readiness_score(
    *,
    topics: Sequence[str],
    profile: LearnerProfile,
    adaptive_graph: AdaptiveGraph,
) -> float:
    """Prefer questions whose prerequisites are at least partly in place.

    Args:
        topics: Candidate topic ids attached to a question.
        profile: Current learner profile.
        adaptive_graph: KG-backed helper used to inspect prerequisites.

    Returns:
        Mean readiness over the prerequisite chains of the covered topics.
    """

    readiness_values: list[float] = []
    for topic in topics:
        prerequisites = adaptive_graph.prerequisite_topics(topic)
        if not prerequisites:
            readiness_values.append(0.65)
            continue
        readiness_values.append(
            _mean_or_default(
                [profile.mastery_for_topic(prerequisite) for prerequisite in prerequisites],
                default=0.0,
            )
        )
    return _mean_or_default(readiness_values, default=0.55)


def topic_coverage_score(
    *,
    topics: Sequence[str],
    profile: LearnerProfile,
) -> float:
    """Prefer under-practiced topics over already saturated ones.

    Args:
        topics: Candidate topic ids associated with a question.
        profile: Current learner profile.

    Returns:
        Ratio of covered topics that have never been attempted before.
    """

    if not topics:
        return 0.40
    unseen_count = sum(1 for topic in topics if profile.topic_attempts.get(topic, 0) == 0)
    return unseen_count / len(topics)


def priority_match_score(
    *,
    topics: Sequence[str],
    priority_topics: Iterable[str],
    adaptive_graph: AdaptiveGraph,
) -> float:
    """Boost questions that directly hit current weak topics or their close neighbors.

    Args:
        topics: Candidate topic ids associated with a question.
        priority_topics: Topics that the selector currently wants to target.
        adaptive_graph: KG-backed helper used to expand related neighbors.

    Returns:
        A priority score where direct matches score highest, KG-neighbor matches
        score moderately, and unrelated questions receive the lowest score.
    """

    priority_set = set(priority_topics)
    if not priority_set:
        return 0.50
    if any(topic in priority_set for topic in topics):
        return 1.0

    related_priority: set[str] = set()
    for priority_topic in priority_set:
        related_priority.update(adaptive_graph.related_topics(priority_topic))

    if any(topic in related_priority for topic in topics):
        return 0.70
    return 0.20
