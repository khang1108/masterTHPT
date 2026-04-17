"""Unit tests for the LangGraph-backed adaptive agent wrapper.

These tests focus on the stateful orchestration layer around ``AdaptiveService``
rather than the lower-level scoring math that is already covered elsewhere.
"""

from __future__ import annotations

from master.agents.adaptive.agent import AdaptiveAgent
from master.agents.common.message import Intent, MessageRequest


def test_adaptive_agent_creates_profile_when_missing() -> None:
    """The workflow should bootstrap a learner profile from the request payload."""

    agent = AdaptiveAgent()

    result = agent.run(
        {
            "request": MessageRequest(
                intent=Intent.EXAM_PRACTICE,
                student_id="student-1",
            ),
        }
    )

    profile = result["learner_profile"]

    assert profile.student_id == "student-1"
    assert profile.total_attempts == 0
    assert profile.total_correct == 0
    assert result["profile_updates"]["attempts_processed"] == 0
    assert result["selected_questions"] == []


def test_adaptive_agent_updates_profile_and_excludes_answered_questions() -> None:
    """Answered questions should update the profile and be excluded from re-selection."""

    agent = AdaptiveAgent()

    result = agent.run(
        {
            "request": MessageRequest(
                intent=Intent.EXAM_PRACTICE,
                student_id="student-1",
            ),
            "questions": [
                {
                    "id": "q-1",
                    "content": "Question 1",
                    "correct_answer": "A",
                    "difficulty_a": 1.0,
                    "difficulty_b": 0.2,
                    "topic_tags": ["algebra.linear"],
                },
                {
                    "id": "q-2",
                    "content": "Question 2",
                    "correct_answer": "B",
                    "difficulty_a": 1.0,
                    "difficulty_b": 0.1,
                    "topic_tags": ["algebra.linear"],
                },
                {
                    "id": "q-3",
                    "content": "Question 3",
                    "correct_answer": "C",
                    "difficulty_a": 1.0,
                    "difficulty_b": 0.0,
                    "topic_tags": ["geometry.circle"],
                },
            ],
            "student_answers": [
                {
                    "question_id": "q-1",
                    "answer": "D",
                }
            ],
        }
    )

    profile = result["learner_profile"]
    update_summary = result["profile_updates"]["updates"][0]
    selected_ids = [question.question_id for question in result["selected_questions"]]

    assert result["profile_updates"]["attempts_processed"] == 1
    assert profile.total_attempts == 1
    assert profile.total_correct == 0
    assert profile.theta < 0.0
    assert profile.last_updated_question_id == "q-1"
    assert update_summary["question_id"] == "q-1"
    assert update_summary["is_correct"] is False
    assert update_summary["updated_topics"]["algebra.linear"] < 0.25
    assert selected_ids == ["q-2", "q-3"]


def test_adaptive_agent_normalizes_answers_before_grading() -> None:
    """Answer comparison should ignore casing and surrounding whitespace."""

    agent = AdaptiveAgent()

    result = agent.run(
        {
            "request": MessageRequest(
                intent=Intent.EXAM_PRACTICE,
                student_id="student-2",
            ),
            "questions": [
                {
                    "id": "q-1",
                    "content": "Question 1",
                    "correct_answer": "A",
                    "difficulty_a": 1.0,
                    "difficulty_b": 0.0,
                    "topic_tags": ["logic.basic"],
                }
            ],
            "student_answers": [
                {
                    "question_id": "q-1",
                    "answer": "  a  ",
                }
            ],
        }
    )

    profile = result["learner_profile"]
    update_summary = result["profile_updates"]["updates"][0]

    assert profile.total_attempts == 1
    assert profile.total_correct == 1
    assert profile.theta > 0.0
    assert update_summary["is_correct"] is True
    assert result["selected_questions"] == []
