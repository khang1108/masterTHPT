"""Focused unit tests for the adaptive learner-model MVP.

These tests cover the statistical core first because the adaptive selector is
only trustworthy if the underlying learner-state updates behave as expected.
"""

from __future__ import annotations

from master.agents.adaptive.bkt import BKTEngine, BKTParams
from master.agents.adaptive.profile_builder import AdaptiveAttempt
from master.agents.adaptive.service import AdaptiveService


def test_bkt_updates_mastery_in_expected_direction() -> None:
    """A correct answer should increase mastery while an incorrect one lowers it."""

    params = BKTParams(p_init=0.25, p_learn=0.15, p_slip=0.10, p_guess=0.20)
    engine = BKTEngine(params=params)

    correct_mastery = engine.update_mastery(0.25, True)
    incorrect_mastery = engine.update_mastery(0.25, False)

    assert correct_mastery > 0.25
    assert incorrect_mastery < 0.25


def test_adaptive_service_updates_profile_state() -> None:
    """A single attempt should update counts, ability, mastery, and recency."""

    service = AdaptiveService()
    profile = service.create_profile("student-1", topic_tags=["algebra.linear"])

    updated = service.update_profile(
        profile,
        AdaptiveAttempt(
            student_id="student-1",
            question_id="q-1",
            is_correct=True,
            topic_tags=["algebra.linear"],
            difficulty_b=0.2,
        ),
    )

    assert updated.total_attempts == 1
    assert updated.total_correct == 1
    assert updated.theta > profile.theta
    assert updated.topic_attempts["algebra.linear"] == 1
    assert updated.topic_correct["algebra.linear"] == 1
    assert updated.topic_mastery["algebra.linear"] > profile.mastery_for_topic(
        "algebra.linear"
    )
    assert updated.recent_question_ids[-1] == "q-1"


def test_recommend_questions_prioritizes_weak_topics_near_theta() -> None:
    """Weak topics near the learner ability should outrank poor-fit candidates."""

    service = AdaptiveService()
    profile = service.create_profile(
        "student-1",
        topic_tags=["algebra.linear", "geometry.circle"],
    )
    profile.topic_mastery["algebra.linear"] = 0.30
    profile.topic_mastery["geometry.circle"] = 0.85
    profile.theta = 0.15
    profile.recent_question_ids = ["q-recent"]
    profile.recent_topics = ["geometry.circle"]

    ranked = service.recommend_questions(
        profile,
        question_bank=[
            {
                "id": "q-weak-fit",
                "topic_tags": ["algebra.linear"],
                "difficulty_b": 0.10,
            },
            {
                "id": "q-strong-fit",
                "topic_tags": ["geometry.circle"],
                "difficulty_b": 0.10,
            },
            {
                "id": "q-weak-hard",
                "topic_tags": ["algebra.linear"],
                "difficulty_b": 2.20,
            },
        ],
        limit=3,
    )

    assert [item.question_id for item in ranked] == [
        "q-weak-fit",
        "q-strong-fit",
        "q-weak-hard",
    ]
    assert ranked[0].rationale
