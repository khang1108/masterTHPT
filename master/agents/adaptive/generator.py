"""LLM-backed adaptive question generation with mandatory DB context retrieval."""

from __future__ import annotations

import json
from typing import Any, Sequence
from uuid import uuid4

from master.agents.baseagent import BaseAgent
from master.agents.common.langsmith import build_langsmith_invoke_config
from master.agents.common.learner_profile import LearnerProfile
from master.agents.common.llm_client import LLMClient
from master.agents.common.message import ExamQuestion, MessageRequest
from master.agents.common.prompt import adaptive_generate_questions_prompt

from .question_gen import GeneratedQuestionBatch


class AdaptiveQuestionGenerator(BaseAgent):
    """Generate new THPTQG-style questions from learner state and RAG context."""

    def __init__(self, llm=None) -> None:
        """Create the generator with an optional injected chat model."""

        super().__init__(agent_role="Adaptive")

        self._llm = llm
        self.system_prompt = """
        Bạn là một AI Question Generator chuyên tạo câu hỏi thi THPT Quốc Gia (THPTQG).

        VAI TRÒ:
            - Sinh câu hỏi mới dựa trên:
            + LearnerProfile (trình độ, điểm yếu, điểm mạnh)
            + Target topics
            + RAG context từ database (bắt buộc sử dụng)
            - Mục tiêu: giúp học sinh cải thiện kiến thức theo hướng cá nhân hóa.

        NGUYÊN TẮC CỐT LÕI:
            - KHÔNG được copy hoặc paraphrase gần giống câu hỏi trong RAG context.
            - PHẢI giữ phong cách đề thi THPTQG:
            + câu lệnh rõ ràng
            + đúng chuẩn chương trình phổ thông
            - Độ khó phải phù hợp learner_theta:
            + ưu tiên vùng “học hiệu quả” (không quá dễ, không quá khó)
            - Ưu tiên sinh câu vào weak_topics trước.
        Các loại câu hỏi được hỗ trợ:

        1. "type" có 3 giá trị:
            - "multiple_choice": câu trắc nghiệm 4 lựa chọn A, B, C, D
            - "true_false": câu đúng/sai gồm nhiều mệnh đề (a), b), c), d)
            - "short_ans": câu tự luận, không có lựa chọn

        Quy tắc cho từng field:
            1. "content":
                - Là toàn bộ nội dung câu hỏi.
                - Bao gồm cả biểu thức LaTeX nếu có.
                - Không chứa đáp án hoặc lời giải.
                - Không chứa các lựa chọn.

            2. "type":
                - Phải là một trong ba giá trị: "multiple_choice", "true_false", "short_ans".
                - Phải phản ánh đúng cấu trúc câu hỏi thực tế.

            3. "options":
                - "multiple_choice":
                    + Là mảng gồm đúng 4 phần tử.
                    + Giữ nguyên định dạng A., B., C., D. như trong đề.
                - "true_false":
                    + Là mảng các mệnh đề.
                    + Mỗi phần tử tương ứng một mệnh đề (a), b), c), d), ...
                    + Giữ nguyên nội dung từng mệnh đề.
                - "short_ans":
                    + Giá trị phải là null.
                    + Không được chứa mảng rỗng.

        RÀNG BUỘC BẮT BUỘC:
        - Chỉ trả về JSON hợp lệ theo schema.
        - Không giải thích.
        - Không thêm text ngoài JSON.
        - Không dùng markdown.
        - Không dùng code fence.
        - Không thêm field ngoài schema.
        - Không được suy đoán hoặc tự tạo thêm lựa chọn nếu đề không có.
        - Không được gộp nhiều câu thành một.
        - Không được tách một câu thành nhiều câu nếu đề không thể hiện như vậy.

        RÀNG BUỘC NỘI DUNG:
        - Mỗi câu:
        + có đúng 4 options
        + correct_answer phải nằm trong options
        + content phải rõ nghĩa, không mơ hồ
        - Không tạo câu hỏi vô nghĩa hoặc không giải được.
        - Không sinh câu quá giống nhau.
        - topic_tags phải phản ánh đúng nội dung câu hỏi.
        - difficulty_b phải hợp lý với learner (không random).

        SỬ DỤNG RAG CONTEXT:
        - Dùng context để:
        + học style ra đề
        + hiểu phân bố độ khó
        + hiểu cách đặt bẫy / distractor
        - KHÔNG được:
        + copy câu
        + đổi số đơn giản từ context
        + giữ cấu trúc identical

        PHÂN PHỐI CÂU HỎI:
        - Nếu số lượng >= 3:
        + ưu tiên đa dạng dạng câu
        - Nếu ít:
        + ưu tiên câu đánh đúng trọng tâm yếu

        SCHEMA OUTPUT:
        {
        "questions": [
            {
            "type": "multiple_choice | true_false | short_ans",
            "content": "string",
            "content_latex": "string | null",
            "options": ["string", "string", "string", "string"],
            "correct_answer": "string",
            "discrimination_a": "number",
            "difficulty_b": "number",
            "topic_tags": ["string"],
            "max_score": "number"
            }
        ]
        }

        QUY TẮC CUỐI:
        - Output phải parse được bằng JSON parser.
        - Nếu không chắc, ưu tiên đơn giản hóa câu hỏi thay vì tạo sai.
        """

    def _get_llm(self):
        """Lazily build the default LLM used for adaptive question generation."""

        if self._llm is None:
            self._llm = LLMClient.chat_model(
                agent_role="adaptive",
                temperature=0.6,
            )
        return self._llm

    @staticmethod
    def _response_text(response: Any) -> str:
        """Normalize chat-model response content into plain text."""

        content = getattr(response, "content", response)
        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if isinstance(item, dict):
                    parts.append(str(item.get("text", "")))
                else:
                    parts.append(str(item))
            content = "".join(parts)
        return str(content).strip()

    async def run(self, input: str) -> str:
        """BaseAgent compatibility entrypoint for simple chat-style calls."""

        llm = self._get_llm()
        response = await llm.ainvoke(
            self.build_messages(input),
            build_langsmith_invoke_config(
                run_name="AdaptiveQuestionGenerator.run",
                agent_role="adaptive",
                extra_tags=["adaptive", "generator", "chat"],
            ),
        )
        return self._response_text(response)

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
        prompt = adaptive_generate_questions_prompt(
            limit=limit,
            learner_profile_json=profile.model_dump_json(),
            target_topics_json=json.dumps(target_topics, ensure_ascii=False),
            learner_request=learner_request,
            rag_context_json=json.dumps(
                self._context_payload(context_questions),
                ensure_ascii=False,
            ),
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
            self.build_messages(prompt),
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
            question_id = f"generated-{profile.student_id}-{uuid4().hex[:10]}-{index}"
            generated_questions.append(
                ExamQuestion(
                    question_id=question_id,
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
