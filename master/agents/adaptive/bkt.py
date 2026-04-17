"""Bayesian Knowledge Tracing primitives for per-topic mastery updates.

This module defines the configuration and execution engine for the BKT portion
of the adaptive stack. The main idea is simple:
- ``BKTParams`` stores the tunable probabilities.
- ``BKTEngine`` applies one-step mastery updates after each learner response.

The module also keeps a small compatibility wrapper so higher-level code can
transition gradually from function-style calls to the engine-based API.
"""

from __future__ import annotations

from pydantic import BaseModel


def _clamp_probability(
    value: float,
    lower: float = 0.001,
    upper: float = 0.999,
) -> float:
    """Clamp a probability into a numerically stable closed interval.

    Args:
        value: Raw probability-like value that may drift outside valid bounds.
        lower: Minimum allowed probability.
        upper: Maximum allowed probability.

    Returns:
        The input restricted to the inclusive ``[lower, upper]`` range.
    """

    return max(lower, min(upper, value))


class BKTParams(BaseModel):
    """Hyperparameters used by Bayesian Knowledge Tracing.

    Attributes:
        p_init: Xác suất học sinh biết skill này trước đó.
        p_learn: Xác suất để học sinh có thể áp dụng kiến thức sau khi đã học.
        p_slip: Xác suất để học sinh mắc sai lầm khi áp dụng kiến thức.
        p_guess: Xác suất để học sinh có thể làm đúng nhưng chưa học skill đó.
    """

    p_init: float = 0.25
    p_learn: float = 0.15
    p_slip: float = 0.10
    p_guess: float = 0.20


class BKTEngine:
    """Engine that applies BKT belief updates for learner mastery.

    A single instance can be reused across many learners because it only stores
    model hyperparameters. The per-learner state remains outside the engine in
    the learner profile.
    """

    def __init__(self, params: BKTParams | None = None) -> None:
        """Construct a BKT engine.

        Args:
            params: Optional parameter override for the engine. If omitted,
                default BKT settings are used.
        """

        self.params = params or BKTParams()

    def posterior_given_observation(
        self,
        prior_mastery: float,
        is_correct: bool,
    ) -> float:
        """Cập nhật lại khả năng nắm vững kiến thức dựa trên phản hồi mới nhất.

        Sử dụng công thức Bayes trước khi chuyển đổi quá trình học tập.

        Args:
            prior_mastery: Khả năng nắm vững của người học trước khi gặp câu này.
            is_correct: Người học có trả lời đúng.

        Returns:
            Khả năng nắm vững sau khi đã được huấn luyện về phản ứng.
        """

        prior = _clamp_probability(prior_mastery) # Ép xác suất về khoản [0.001, 0.999]

        if is_correct:
            # Áp dụng công thức để tính được P(learner_(n_1) | correct_n)
            # P(known[n-1]) * (1 - p_slip) = tử số
            # tử số + (1 - P(known[n-1])) * P(gues)
            numerator = prior * (1.0 - self.params.p_slip)
            denominator = numerator + (1.0 - prior) * self.params.p_guess
        else:
            # Còn nếu làm sai thì có công thức là
            # Tử số = P(known[n-1]) * P_slip
            # Mẫu số = tử số + (1 - P(known[n-1]) * (1 - P(guess))
            numerator = prior * self.params.p_slip
            denominator = numerator + (1.0 - prior) * (1.0 - self.params.p_guess)

        return _clamp_probability(numerator / max(denominator, 1e-9)) 

    def apply_learning_transition(self, posterior_mastery: float) -> float:
        """Tính toán xác suất khi học sinh đã học skill này tại lần thứ n.

        Args:
            posterior_mastery: Mastery belief after conditioning on correctness.

        Returns:
            Final mastery after allowing a chance that learning happened during
            the interaction.
        """

        posterior = _clamp_probability(posterior_mastery)
        # Công thức để là:
        # P(learn[n] | answer[n]) = P(learn[n-1] | answer[n]) + (1 - P(learn[n-1] | answer[n])) * P(will learn)
        transitioned = posterior + (1.0 - posterior) * self.params.p_learn
        return _clamp_probability(transitioned)

    def update_mastery(self, prior_mastery: float, is_correct: bool) -> float:
        """Perform the full one-step BKT mastery update.

        Args:
            prior_mastery: Learner mastery belief before the attempt.
            is_correct: Whether the learner answered correctly.

        Returns:
            The new mastery estimate after evidence and learning transition.
        """

        posterior = self.posterior_given_observation(prior_mastery, is_correct)
        return self.apply_learning_transition(posterior)


# Backward-compatible alias so the rest of the codebase can migrate safely.
BKTParameters = BKTParams


def update_mastery(
    prior_mastery: float,
    is_correct: bool,
    params: BKTParams | None = None,
) -> float:
    """Compatibility wrapper for one-step BKT updates.

    Args:
        prior_mastery: Learner mastery belief before the attempt.
        is_correct: Whether the learner answered correctly.
        params: Optional BKT parameter override.

    Returns:
        The updated mastery estimate produced by ``BKTEngine``.
    """

    return BKTEngine(params=params).update_mastery(prior_mastery, is_correct)
