"""Unit tests for the LangGraph-backed adaptive agent wrapper.

These tests focus on the stateful orchestration layer around ``AdaptiveService``
rather than the lower-level scoring math that is already covered elsewhere.
"""

from __future__ import annotations

from master.agents.adaptive.agent import AdaptiveAgent
from master.agents.common.learner_profile import LearnerProfile
from master.agents.common.message import ExamQuestion, Intent, MessageRequest


class FakeAdaptiveRepository:
    """In-memory repository used to verify DB hydration/persistence behavior."""

    def __init__(
        self,
        *,
        questions=None,
        profile: LearnerProfile | None = None,
    ) -> None:
        self.questions = list(questions or [])
        self.profile = profile
        self.saved_profiles: list[LearnerProfile] = []
        self.last_question_query = None
        self.last_rag_query = None

    async def get_learner_profile(self, student_id: str) -> LearnerProfile | None:
        if self.profile and self.profile.student_id == student_id:
            return self.profile.model_copy(deep=True)
        return None

    async def upsert_learner_profile(self, profile: LearnerProfile) -> None:
        self.profile = profile.model_copy(deep=True)
        self.saved_profiles.append(profile.model_copy(deep=True))

    async def get_questions(
        self,
        *,
        exam_id: str | None = None,
        question_ids=None,
        topic_tags=None,
        exclude_question_ids=None,
        limit: int = 100,
    ):
        self.last_question_query = {
            "exam_id": exam_id,
            "question_ids": list(question_ids or []),
            "topic_tags": list(topic_tags or []),
            "exclude_question_ids": list(exclude_question_ids or []),
            "limit": limit,
        }
        excluded = set(exclude_question_ids or [])
        return [
            question
            for question in self.questions
            if question.get("id") not in excluded and question.get("question_id") not in excluded
        ]

    async def get_rag_question_context(
        self,
        *,
        exam_id: str | None = None,
        question_ids=None,
        topic_tags=None,
        exclude_question_ids=None,
        limit: int = 8,
    ):
        self.last_rag_query = {
            "exam_id": exam_id,
            "question_ids": list(question_ids or []),
            "topic_tags": list(topic_tags or []),
            "exclude_question_ids": list(exclude_question_ids or []),
            "limit": limit,
        }
        excluded = set(exclude_question_ids or [])
        return [
            ExamQuestion.model_validate(question)
            for question in self.questions
            if question.get("id") not in excluded and question.get("question_id") not in excluded
        ][:limit]


class FakeQuestionGenerator:
    """Stub generator that captures RAG context and returns deterministic questions."""

    def __init__(self) -> None:
        self.last_call = None

    def generate_questions(
        self,
        *,
        request: MessageRequest | None,
        profile: LearnerProfile,
        context_questions,
        limit: int = 3,
    ):
        self.last_call = {
            "request": request,
            "profile": profile,
            "context_question_ids": [question.question_id for question in context_questions],
            "limit": limit,
        }
        return [
            ExamQuestion(
                question_id=f"generated-{profile.student_id}-{index}",
                content=f"Cau sinh moi {index}",
                options=["A", "B", "C", "D"],
                correct_answer="A",
                topic_tags=list(profile.weak_topics() or ["geometry.circle"]),
                difficulty_a=1.0,
                difficulty_b=0.1,
            )
            for index in range(1, limit + 1)
        ]


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


def test_adaptive_agent_loads_profile_and_questions_from_repository() -> None:
    """Missing state should be hydrated from the adaptive repository tools."""

    repository = FakeAdaptiveRepository(
        profile=LearnerProfile(
            student_id="student-3",
            topic_mastery={"geometry.circle": 0.2},
        ),
        questions=[
            {
                "id": "q-10",
                "content": "Question 10",
                "correct_answer": "A",
                "difficulty_a": 1.0,
                "difficulty_b": 0.1,
                "topic_tags": ["geometry.circle"],
            },
            {
                "id": "q-11",
                "content": "Question 11",
                "correct_answer": "B",
                "difficulty_a": 1.0,
                "difficulty_b": 0.0,
                "topic_tags": ["geometry.circle"],
            },
        ],
    )
    agent = AdaptiveAgent(repository=repository)

    result = agent.run(
        {
            "request": MessageRequest(
                intent=Intent.EXAM_PRACTICE,
                student_id="student-3",
                exam_id="exam-123",
                metadata={"question_limit": 25},
            ),
        }
    )

    assert result["learner_profile"].student_id == "student-3"
    assert repository.last_question_query is not None
    assert repository.last_question_query["exam_id"] == "exam-123"
    assert repository.last_question_query["limit"] == 25
    assert {question.question_id for question in result["selected_questions"]} == {
        "q-10",
        "q-11",
    }


def test_adaptive_agent_persists_profile_after_updates() -> None:
    """Processed attempts should be written back to the learner-profile store."""

    repository = FakeAdaptiveRepository()
    agent = AdaptiveAgent(repository=repository)

    result = agent.run(
        {
            "request": MessageRequest(
                intent=Intent.EXAM_PRACTICE,
                student_id="student-4",
            ),
            "questions": [
                {
                    "id": "q-20",
                    "content": "Question 20",
                    "correct_answer": "C",
                    "difficulty_a": 1.0,
                    "difficulty_b": 0.0,
                    "topic_tags": ["algebra.linear"],
                }
            ],
            "student_answers": [
                {
                    "question_id": "q-20",
                    "answer": "C",
                }
            ],
        }
    )

    assert repository.saved_profiles
    persisted = repository.saved_profiles[-1]
    assert persisted.student_id == "student-4"
    assert persisted.total_attempts == 1
    assert persisted.total_correct == 1
    assert persisted.last_updated_question_id == "q-20"
    assert result["learner_profile"].total_correct == 1


def test_adaptive_agent_generates_questions_from_rag_context() -> None:
    """Generation mode should always retrieve DB context before creating new items."""

    repository = FakeAdaptiveRepository(
        profile=LearnerProfile(
            student_id="student-5",
            topic_mastery={"geometry.circle": 0.15},
        ),
        questions=[
            {
                "id": "ctx-1",
                "content": "Cau tham khao 1",
                "correct_answer": "A",
                "difficulty_a": 1.0,
                "difficulty_b": 0.1,
                "topic_tags": ["geometry.circle"],
                "options": ["A", "B", "C", "D"],
            },
            {
                "id": "ctx-2",
                "content": "Cau tham khao 2",
                "correct_answer": "B",
                "difficulty_a": 1.0,
                "difficulty_b": 0.2,
                "topic_tags": ["geometry.circle"],
                "options": ["A", "B", "C", "D"],
            },
        ],
    )
    generator = FakeQuestionGenerator()
    agent = AdaptiveAgent(repository=repository, generator=generator)

    result = agent.run(
        {
            "request": MessageRequest(
                intent=Intent.EXAM_PRACTICE,
                student_id="student-5",
                exam_id="exam-rag-1",
                content="Muon luyen them hinh hoc theo phong cach THPTQG",
                metadata={
                    "generate_questions": True,
                    "generation_limit": 2,
                    "rag_context_limit": 2,
                },
            ),
            "questions": [
                {
                    "id": "local-ignored",
                    "content": "Khong duoc dung lam RAG context",
                    "correct_answer": "A",
                    "options": ["A", "B", "C", "D"],
                    "topic_tags": ["logic.basic"],
                }
            ],
        }
    )

    assert repository.last_rag_query is not None
    assert repository.last_rag_query["exam_id"] == "exam-rag-1"
    assert repository.last_rag_query["limit"] == 2
    assert repository.last_rag_query["topic_tags"] == ["geometry.circle"]
    assert generator.last_call is not None
    assert generator.last_call["context_question_ids"] == ["ctx-1", "ctx-2"]
    assert generator.last_call["limit"] == 2
    assert [question.question_id for question in result["selected_questions"]] == [
        "generated-student-5-1",
        "generated-student-5-2",
    ]
