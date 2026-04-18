"""LLM-backed adaptive question generation with mandatory DB context retrieval."""

from __future__ import annotations

import json
from typing import Any, Sequence

from master.agents.common.langsmith import build_langsmith_invoke_config
from master.agents.common.learner_profile import LearnerProfile
from master.agents.common.llm_client import LLMClient
from master.agents.common.message import ExamQuestion, MessageRequest

from .question_gen import GeneratedQuestionBatch


class AdaptiveQuestionGenerator:
    """Generate new THPTQG-style questions from learner state and RAG context."""

    def __init__(self, llm=None) -> None:
        """Create the generator with an optional injected chat model."""

        self._llm = llm

    def _get_llm(self):
        """Lazily build the default LLM used for adaptive question generation."""

        if self._llm is None:
            self._llm = LLMClient.chat_model(
                agent_role="adaptive",
                temperature=0.6,
            )
        return self._llm

    @staticmethod
    def _context_payload(context_questions: Sequence[ExamQuestion]) -> list[dict[str, Any]]:
        """Serialize retrieved DB questions into a prompt-friendly shape."""

        payload: list[dict[str, Any]] = []
        for question in context_questions:
            payload.append(
                {
                    "question_id": question.question_id,
                    "type": question.type,
                    "content": question.content,
                    "options": question.options,
                    "correct_answer": question.correct_answer,
                    "topic_tags": question.topic_tags,
                    "discrimination_a": question.discrimination_a,
                    "difficulty_b": question.difficulty_b,
                }
            )
        return payload

    @staticmethod
    def _target_topics(
        profile: LearnerProfile,
        requested_topics: Sequence[str] | None = None,
    ) -> list[str]:
        """Choose the prioritized topics for new question generation."""

        explicit = [topic for topic in (requested_topics or []) if topic]
        if explicit:
            return explicit

        weak_topics = profile.weak_topics()
        if weak_topics:
            return weak_topics[:3]

        strong_topics = profile.strong_topics()
        if strong_topics:
            return strong_topics[:2]

        return []

    def generate_questions(
        self,
        *,
        request: MessageRequest | None,
        profile: LearnerProfile,
        context_questions: Sequence[ExamQuestion],
        limit: int = 3,
    ) -> list[ExamQuestion]:
        """Generate new questions using THPTQG-style context retrieved from DB.

        Args:
            request: Current adaptive request, used for optional learner intent.
            profile: Learner profile guiding topic and difficulty targeting.
            context_questions: Retrieved question corpus from MongoDB. This is
                mandatory RAG context, not optional seasoning.
            limit: Number of questions to generate.

        Returns:
            A list of normalized generated ``ExamQuestion`` objects.
        """

        if not context_questions or limit <= 0:
            return []

        metadata = request.metadata if request else {}
        target_topics = self._target_topics(profile, metadata.get("target_topics"))
        learner_request = (
            request.content
            if request and getattr(request, "content", None)
            else request.student_message if request else ""
        )
        prompt = (
            "Ban la giao vien ra de THPT Quoc Gia. "
            "Nhiem vu la SINH cau hoi moi cho hoc sinh dua tren LearnerProfile, "
            "nhung BAT BUOC phai dua vao bo cau hoi truy xuat tu database lam RAG context. "
            "Khong sao chep nguyen van context, nhung phai giu phong cach de thi THPTQG: "
            "cau lenh ro rang, 4 lua chon, 1 dap an dung, muc do kho hop ly, "
            "co xu huong danh vao cac chu de hoc sinh con yeu.\n\n"
            f"So cau can sinh: {limit}\n"
            f"LearnerProfile: {profile.model_dump_json()}\n"
            f"Target topics uu tien: {json.dumps(target_topics, ensure_ascii=False)}\n"
            f"Yeu cau bo sung cua nguoi dung: {learner_request or 'Khong co'}\n\n"
            "RAG CONTEXT TU DATABASE (tham khao phong cach, topic, do kho):\n"
            f"{json.dumps(self._context_payload(context_questions), ensure_ascii=False)}\n\n"
            "Rang buoc dau ra:\n"
            "- Chi sinh cau moi, khong lap lai y nguyen van tu context.\n"
            "- Moi cau co 4 options.\n"
            "- correct_answer phai khop mot trong 4 options.\n"
            "- topic_tags phai phan anh dung chu de muc tieu.\n"
            "- difficulty_b nen xap xi nang luc hien tai, uu tien vung hoc tap hieu qua.\n"
            "- Khong giai thich ngoai schema."
        )

        llm = self._get_llm()
        try:
            structured_llm = llm.with_structured_output(
                GeneratedQuestionBatch,
                method="function_calling",
            )
        except TypeError:
            # Fallback for providers that do not support ``method`` override.
            structured_llm = llm.with_structured_output(GeneratedQuestionBatch)

        result: GeneratedQuestionBatch = structured_llm.invoke(
            prompt,
            build_langsmith_invoke_config(
                run_name="AdaptiveQuestionGenerator.generate_questions",
                agent_role="adaptive",
                extra_tags=["adaptive", "generate-questions", "rag"],
                extra_metadata={
                    "generation_limit": limit,
                    "context_count": len(context_questions),
                    "target_topics": target_topics,
                },
            ),
        )

        generated_questions: list[ExamQuestion] = []
        for index, item in enumerate(result.questions[:limit], start=1):
            generated_questions.append(
                ExamQuestion(
                    question_id=f"generated-{profile.student_id}-{index}",
                    exam_id=request.exam_id if request else "adaptive-generated",
                    question_index=index,
                    type=item.type,
                    content=item.content,
                    content_latex=item.content_latex,
                    options=item.options,
                    correct_answer=item.correct_answer,
                    discrimination_a=item.discrimination_a,
                    difficulty_b=item.difficulty_b,
                    topic_tags=item.topic_tags or target_topics,
                    max_score=item.max_score,
                )
            )
        return generated_questions
