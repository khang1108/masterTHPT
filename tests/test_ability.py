"""Unit tests for the adaptive global-ability engine."""

from __future__ import annotations

from master.agents.adaptive.ability import (
    AbilityParameters,
    expected_correct_probability,
    update_theta_and_difficulty,
)


def test_probability_is_strictly_between_zero_and_one() -> None:
    """The logistic response curve should never return invalid probabilities."""

    probability = expected_correct_probability(theta=0.0, difficulty=0.0)

    assert 0.0 < probability < 1.0


def test_correct_answer_increases_theta() -> None:
    """A better-than-expected result should move learner ability upward."""

    result = update_theta_and_difficulty(
        theta=0.0,
        difficulty=0.0,
        is_correct=True,
    )

    assert result.theta > 0.0
    assert result.residual > 0.0


def test_wrong_answer_decreases_theta() -> None:
    """A worse-than-expected result should move learner ability downward."""

    result = update_theta_and_difficulty(
        theta=0.0,
        difficulty=0.0,
        is_correct=False,
    )

    assert result.theta < 0.0
    assert result.residual < 0.0


def test_harder_correct_answer_yields_stronger_positive_update() -> None:
    """Unexpected success on a harder item should boost theta more strongly."""

    easy = update_theta_and_difficulty(
        theta=0.0,
        difficulty=-1.0,
        is_correct=True,
    )
    hard = update_theta_and_difficulty(
        theta=0.0,
        difficulty=1.0,
        is_correct=True,
    )

    assert hard.theta > easy.theta


def test_item_difficulty_stays_fixed_by_default() -> None:
    """Item updates are opt-in until persistence is added elsewhere."""

    result = update_theta_and_difficulty(
        theta=0.0,
        difficulty=0.5,
        is_correct=True,
    )

    assert result.difficulty == 0.5


def test_item_difficulty_updates_when_enabled() -> None:
    """Optional item updates should move difficulty opposite to learner surprise."""

    params = AbilityParameters(student_k=0.35, question_k=0.15)
    result = update_theta_and_difficulty(
        theta=0.0,
        difficulty=1.0,
        is_correct=True,
        params=params,
        update_item=True,
    )

    assert result.difficulty < 1.0
