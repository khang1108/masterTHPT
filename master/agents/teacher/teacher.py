from typing import Optional, Annotated, Any, List
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from master.agents import BaseAgent
from master.agents.common.state import AgentState
from master.common.message import Solution
from master.agents.common.message import MessageRequest, StudentAnswer, Intent
from master.agents.common.tools import ToolsRegistry
from master.agents.common.langsmith import build_langsmith_invoke_config
from master.agents.common.llm_client import LLMClient
from master.agents.common.prompt import (
    teacher_system_prompt,
    teacher_preprocess_prompt,
    teacher_counter_evidence_prompt,
    teacher_tool_research_prompt,
    teacher_hint_prompt,
    teacher_review_mistake_prompt,
)
from master.logging.logger import logger

import json
import os
import asyncio
import re

load_dotenv(override=True)
BATCH_SIZE = 3

# ── Pydantic Models ────────────────────────────────────────────────────────────

class Evaluate(BaseModel):
    """Kết quả chấm nháp của Teacher."""
    question_id: str
    agree: bool = Field(description="Teacher có đồng ý với feedback của Verifier không? Nếu feedback của Verifier để trống thì điền false.")
    confidence: float = 0.5
    correct_answer: Optional[str] = Field(
        default=None,
        description=(
            "Đáp án đúng theo type của câu hỏi. "
            "multiple_choice: chỉ A/B/C/D; "
            "true_false: chuỗi T/F theo từng ý, ví dụ 'T, T, F, T'; "
            "short_ans hoặc short_answer: chuỗi số thuần như '0.33' hoặc '2'. "
            "Nếu không xác định được thì để null."
        ),
    )
    reasoning: str =  Field(description="Giải thích ngắn gọn về lý do đồng ý hay không đồng ý với đáp án của học sinh, hoặc giải thích cách giải nếu đang ở chế độ PREPROCESS.")         
    feedback: str = Field(description="Phản hồi cụ thể cho học sinh, có thể là gợi ý để cải thiện hoặc lời khen nếu đáp án đúng. Phản hồi phải rõ ràng, thân thiện và mang tính xây dựng.")
    discrimination_a: float = Field(description="Độ phân hóa của câu hỏi để đánh giá học sinh giỏi hay yếu, giá trị từ 0 đến 1, càng cao càng phân biệt tốt.")
    difficulty_b: float = Field(description="Độ khó của câu hỏi, giá trị từ 0 đến 1, càng cao càng khó.")
    topic_tags: list[str] = Field(default_factory=list, description="Danh sách topic tag ứng viên cho câu hỏi, sẽ được canonicalize qua knowledge graph.")

class EvaluateBatch(BaseModel):
    results: list[Evaluate]


# ── Teacher Agent ──────────────────────────────────────────────────────────────

class TeacherAgent(ToolsRegistry, BaseAgent):
    def __init__(self):
        super().__init__(agent_role="Teacher")
        self.system_prompt = teacher_system_prompt()
        self._llm        = None
        self._llm_with_single_output = None
        self._llm_with_batch_output = None
        self._memory     = MemorySaver()
        self.graph       = None
        self.system_prompt = """
        Bạn là một AI agent hỗ trợ học sinh THPT Việt Nam trong việc học Toán.

        Bạn phải luôn trả về đúng định dạng output mà hệ thống yêu cầu.
        Ưu tiên cao nhất là:
        1. Đúng schema output
        2. Đúng nội dung toán học
        3. Rõ ràng, phù hợp trình độ học sinh

        YÊU CẦU OUTPUT BẮT BUỘC:
        - Chỉ trả về JSON hợp lệ.
        - Không trả thêm bất kỳ văn bản nào ngoài JSON.
        - Không dùng markdown.
        - Không bọc trong ```json.
        - Trả đầy đủ kết quả cho mọi question_id, không bỏ sót.
        - Mỗi question_id đi kèm đúng 1 kết quả.
        - confidence phải nằm trong khoảng [0, 1].
        - discrimination_a và difficulty_b phải nằm trong khoảng [0, 1].
        - Nếu không xác định được correct_answer thì trả chuỗi rỗng "".
        - Luôn giữ nguyên question_id từ input.
        - Luôn trả đủ tất cả field trong schema.

        Schema đầu ra bắt buộc:

        {
        "results": [
            {
            "question_id": "string",
            "agree": boolean,
            "confidence": number,
            "correct_answer": "string",
            "reasoning": "string",
            "feedback": "string",
            "discrimination_a": number,
            "difficulty_b": number
            }
        ]
        }

        Ý nghĩa các field:
        - question_id: ID câu hỏi, giữ nguyên từ input.
        - agree:
        - Nếu là Teacher: thể hiện bạn đồng ý với đánh giá hiện tại hoặc tin rằng kết luận của bạn là hợp lý.
        - Nếu là Verifier: thể hiện bạn đồng ý với đánh giá của Teacher.
        - confidence: mức độ chắc chắn từ 0 đến 1.
        - correct_answer: đáp án đúng nếu xác định được.
        - reasoning: giải thích học thuật ngắn gọn, rõ ràng, đúng bản chất toán học.
        - feedback: phản hồi trực tiếp cho học sinh, dễ hiểu, mang tính hướng dẫn.
        - discrimination_a: độ phân biệt của câu hỏi, từ 0 đến 1.
        - difficulty_b: độ khó của câu hỏi, từ 0 đến 1.

        Nhiệm vụ của bạn là:
        - đọc đề bài Toán học do người dùng cung cấp
        - phân tích lời giải hoặc câu trả lời của học sinh
        - đưa ra gợi ý khi học sinh chưa muốn xem lời giải đầy đủ
        - trình bày lời giải tự luận đầy đủ, từng bước rõ ràng khi cần
        - phát hiện, chỉ ra, và giải thích các lỗi sai trong lập luận hoặc tính toán của học sinh
        - điều chỉnh mức độ giải thích phù hợp với trình độ học sinh

        Quy tắc bắt buộc:
        - Không dùng icon, emoji, ký hiệu trang trí.
        - Luôn trình bày theo văn phong sư phạm, rõ ràng, mạch lạc, dễ hiểu.
        - Không bỏ bước quan trọng trong suy luận.
        - Không đưa ra đáp án cuối cùng mà thiếu giải thích.
        - Nếu là Verifier, ưu tiên ngắn gọn, đúng schema, không dài dòng.
        - Nếu đề bài thiếu dữ kiện hoặc mơ hồ, phải nói rõ chỗ thiếu hoặc mơ hồ, không tự ý bịa thêm dữ kiện.
        - Nếu có nhiều cách giải, ưu tiên cách phù hợp với chương trình phổ thông và dễ hiểu với học sinh.
        - Khi dùng công thức hoặc định lý, hãy nêu rõ tên và lý do áp dụng.

        Quy tắc theo tình huống:
        - Nếu học sinh yêu cầu hint:
        - Không giải toàn bộ ngay.
        - Chỉ đưa gợi ý vừa đủ để học sinh tự làm tiếp.
        - feedback nên là gợi ý theo từng mức nếu phù hợp:
            - Hint 1: gợi ý định hướng
            - Hint 2: gợi ý phương pháp
            - Hint 3: gợi ý bước làm tiếp theo

        - Nếu học sinh đưa lời giải sai:
        - chỉ ra bước sai
        - giải thích vì sao sai
        - nêu cách sửa đúng
        - nếu cần, trình bày lại lời giải đúng từ chỗ sai đó

        - Nếu người dùng gửi cả bài làm của học sinh:
        - nhận xét tổng quan
        - chỉ ra đúng/sai ở từng ý
        - phân tích lỗi sai
        - đưa cách sửa
        - trình bày lời giải chuẩn nếu cần
        """

    def _extract_feedback_text(self, response: Any) -> str:
        raw = getattr(response, "content", response)

        if isinstance(raw, list):
            parts: list[str] = []
            for item in raw:
                if isinstance(item, dict):
                    parts.append(str(item.get("text", "")))
                else:
                    parts.append(str(item))
            raw = "".join(parts)

        text = str(raw).strip()
        text = re.sub(r"^```json\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"^```\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return text

        if isinstance(parsed, dict):
            feedback = parsed.get("feedback")
            if isinstance(feedback, str) and feedback.strip():
                return feedback.strip()

        return text

    # ── Setup ──────────────────────────────────────────────────────────────────

    async def setup(self):
        logger.agent_node("Teacher setup started")
        llm = LLMClient.chat_model(
            provider="openai_compatible",
            base_url=os.getenv("FPT_BASE_URL"),
            api_key=os.getenv("FPT_API_KEY"),
            model="gpt-oss-120b",
            max_tokens=8000,
            temperature=0.7,
        )
        logger.info(f"LLM client for Teacher initialized: {os.getenv("FPT_API_KEY")}, {os.getenv("FPT_BASE_URL")}, model={llm.model}")

        await self.setup_tools(llm, bundle="teacher")
        self._llm_with_single_output = self._llm.with_structured_output(Evaluate)
        self._llm_with_batch_output = self._llm.with_structured_output(EvaluateBatch)
        logger.agent_node("Teacher setup completed")

    def teacher_router(self, state: AgentState) -> str:
        request = state["request"]
        intent = request.intent
        current_phase = state.get("phase", "draft")
        round_now = state.get("round", 0)
        max_round = state.get("max_round", 3)
        is_agreed = state.get("is_agreed") or []

        if current_phase == "END":
            return "END"
        if current_phase == "verify":
            # PREPROCESS should always go through Verifier; Verifier decides when to stop.
            if intent == Intent.PREPROCESS.value:
                return "verify"
            if round_now >= max_round or (is_agreed and is_agreed[0] and intent == Intent.REVIEW_MISTAKE.value):
                return "END"
        return "verify"

    async def _run_batch(self, state: AgentState) -> AgentState:
        request = state["request"]
        intent = request.intent
        round_now = state.get("round", 0)
        max_round = state.get("max_round", 3)
        if intent == Intent.PREPROCESS.value:
            is_agreed= []
            solutions = []
            confidence = []
            feedback = []
            discrimination_a = []
            difficulty_b = []
            topic_tags_by_id: dict[str, list[str]] = {}
            
            item_list = request.parser_output or []
            id_to_index = {(item.get("id") or item.get("question_id")): idx for idx, item in enumerate(item_list)} if item_list else {}
            remaining_items = []  # Collect items that still need verification
            db_inserted = 0  # Track total DB inserts this round
            db_saved_total_before = state.get("db_saved_total", 0) or 0
            state_is_agreed = state.get("is_agreed", []) or []
            state_discrimination_a = state.get("discrimination_a", []) or []
            state_difficulty_b = state.get("difficulty_b", []) or []
            state_topic_tags = state.get("topic_tags", []) or []
            state_solutions = state.get("solutions", []) or []
            solution_by_id = {}
            for solution in state_solutions:
                if hasattr(solution, "question_id") and hasattr(solution, "solution"):
                    solution_by_id[solution.question_id] = solution.solution
                elif isinstance(solution, dict):
                    question_id = solution.get("question_id")
                    if question_id:
                        solution_by_id[question_id] = solution.get("solution")
            for question_id, idx in id_to_index.items():
                if idx < len(state_topic_tags):
                    topic_tags_by_id[question_id] = state_topic_tags[idx] or []

            for i in range(0, len(item_list), BATCH_SIZE):
                batch = item_list[i:i + BATCH_SIZE]
                batch_saved = 0
                skip_verify = [
                    question_id
                    for question_id in [(item.get("id") or item.get("question_id")) for item in batch]
                    if (
                        id_to_index.get(question_id) is not None
                        and id_to_index[question_id] < len(state_is_agreed)
                        and state_is_agreed[id_to_index[question_id]]
                    )
                ]

                if skip_verify:
                    batch_map = {(item.get("id") or item.get("question_id")): item for item in batch}
                    for ids in skip_verify:
                        item = batch_map.get(ids)
                        if not item:
                            continue

                        item_index = id_to_index.get(ids)
                        discrimination_a_value = (
                            state_discrimination_a[item_index]
                            if item_index is not None and item_index < len(state_discrimination_a)
                            else None
                        )
                        difficulty_b_value = (
                            state_difficulty_b[item_index]
                            if item_index is not None and item_index < len(state_difficulty_b)
                            else None
                        )
                        correct_answer_value = solution_by_id.get(ids)
                        topic_tags_value = topic_tags_by_id.get(ids) or self.trace_question_topics(
                            question_text=item.get("content", ""),
                            options=item.get("options"),
                        )
                        topic_tags_by_id[ids] = topic_tags_value
                        question_type = (item.get("type") or "").strip().lower()
                        normalized_correct_answer = None

                        # Normalize correct answer based on question type 
                        if question_type == "true_false":
                            expected_count = len(item.get("options") or [])
                            answer_text = str(correct_answer_value or "").strip().upper()
                            tokens = [token.strip() for token in answer_text.split(",") if token.strip()]
                            if tokens and all(token in {"T", "F"} for token in tokens):
                                if expected_count == 0 or len(tokens) == expected_count:
                                    normalized_correct_answer = ", ".join(tokens)
                        elif question_type == "multiple_choice":
                            answer_text = str(correct_answer_value or "").strip().upper()
                            if answer_text in {"A", "B", "C", "D"}:
                                normalized_correct_answer = answer_text
                        elif question_type in {"short_ans", "short_answer"}:
                            answer_text = str(correct_answer_value or "").strip()
                            if re.fullmatch(r"[+-]?(?:\d+(?:\.\d+)?|\.\d+)", answer_text):
                                normalized_correct_answer = answer_text
                        else:
                            normalized_correct_answer = correct_answer_value

                        data = {
                            "question_id": item.get("id") or item.get("question_id"),
                            "exam_id": request.exam_id,
                            "question_index": item["question_index"],
                            "type": item.get("type"),
                            "content": item.get("content"),
                            "options": item.get("options"),
                            "correct_answer": normalized_correct_answer,
                            "has_image": item.get("has_image"),
                            "image_url": item.get("image_url"),
                            "discrimination_a": discrimination_a_value,
                            "difficulty_b": difficulty_b_value,
                            "topic_tags": topic_tags_value,
                        }

                        await self.insert_data("masterthpt", "questions", [data])
                        db_inserted += 1
                        batch_saved += 1
                    self.logger.agent_node(
                        f"Teacher batch {i//BATCH_SIZE + 1}: saved {batch_saved} skipped-verify questions to database"
                    )

                need_verify = [item for item in batch if (item.get("id") or item.get("question_id")) not in skip_verify]
                remaining_items.extend(need_verify)
                if not need_verify:
                    continue

                batch_input_json = json.dumps(need_verify, ensure_ascii=False, indent=2)
                prompt = teacher_preprocess_prompt(batch_input_json)
                responses: EvaluateBatch = await self._llm_with_batch_output.ainvoke(
                    self.build_messages(prompt)
                )
                batch_map = {
                    item.get("id") or item.get("question_id"): item
                    for item in need_verify
                }

                is_agreed.extend([response.agree for response in responses.results])
                solutions.extend([
                    Solution(question_id=response.question_id, solution=response.correct_answer)
                    for response in responses.results
                ])
                confidence.extend([response.confidence for response in responses.results])
                discrimination_a.extend([response.discrimination_a for response in responses.results])
                difficulty_b.extend([response.difficulty_b for response in responses.results])
                for response in responses.results:
                    item = batch_map.get(response.question_id) or {}
                    topic_tags_by_id[response.question_id] = self.trace_question_topics(
                        question_text=item.get("content", ""),
                        options=item.get("options"),
                        candidate_topics=response.topic_tags,
                    )
                feedback.extend([
                    f"Ở câu {response.question_id}: {response.feedback} vì {response.reasoning}"
                    for response in responses.results
                ])
                self.logger.agent_node(f"Preprocess batch {i//BATCH_SIZE + 1} result: {responses}")
                try:
                    research_evidence, _, research_source = await self.run_counter_evidence_then_tool(
                        counter_prompt=teacher_counter_evidence_prompt(batch_input_json),
                        tool_prompt=teacher_tool_research_prompt(batch_input_json),
                        messages_key="Teacher_feedback",
                    )
                except Exception as error:
                    research_evidence = ""
                    research_source = "none"
                    self.logger.warning(
                        f"Teacher research failed for batch {i//BATCH_SIZE + 1}: {error}"
                    )

                if research_evidence:
                    prompt += (
                        f"\nRESEARCH_EVIDENCE ({research_source}, prioritize in reasoning/feedback):\n"
                        f"{research_evidence}\n"
                        "Nếu có bằng chứng từ tool thì phải nhắc ngắn gọn bằng chứng đó trong reasoning hoặc feedback."
                    )
                responses: EvaluateBatch = await self._llm_with_batch_output.ainvoke(
                    self.build_messages(prompt)
                )

                response_by_id = {r.question_id: r for r in responses.results}
                missing = [item for item in need_verify if (item.get("id") or item.get("question_id")) not in response_by_id]
                retry_count = 0
                while missing and retry_count < 2:
                    retry_count += 1
                    self.logger.agent_node(f"Teacher retry {retry_count}: {len(missing)} missing items")
                    retry_json = json.dumps(missing, ensure_ascii=False, indent=2)
                    retry_prompt = teacher_preprocess_prompt(retry_json)
                    if research_evidence:
                        retry_prompt += (
                            f"\nRESEARCH_EVIDENCE ({research_source}, prioritize in reasoning/feedback):\n"
                            f"{research_evidence}\n"
                        )
                    retry_responses: EvaluateBatch = await self._llm_with_batch_output.ainvoke(
                        self.build_messages(retry_prompt)
                    )
                    for r in retry_responses.results:
                        response_by_id[r.question_id] = r
                    missing = [item for item in need_verify if (item.get("id") or item.get("question_id")) not in response_by_id]

                for item in need_verify:
                    item_id = item.get("id") or item.get("question_id")
                    r = response_by_id.get(item_id)
                    if r:
                        is_agreed.append(r.agree)
                        confidence.append(r.confidence)
                        discrimination_a.append(r.discrimination_a)
                        difficulty_b.append(r.difficulty_b)
                        if r.correct_answer is not None and str(r.correct_answer).strip() != "":
                            solutions.append(
                                Solution(question_id=r.question_id, solution=str(r.correct_answer).strip())
                            )
                        feedback.append(f"Ở câu {r.question_id}: {r.feedback} vì {r.reasoning}")
                    else:
                        self.logger.agent_node(f"Teacher: no response for {item_id} after retries")
                        is_agreed.append(False)
                        confidence.append(0.0)
                        discrimination_a.append(0.5)
                        difficulty_b.append(0.5)
                        feedback.append(f"Ở câu {item_id}: Không có phản hồi từ Teacher LLM")
                self.logger.agent_node(
                    f"Teacher batch {i//BATCH_SIZE + 1} summary: "
                    f"{len(response_by_id)}/{len(need_verify)} responses, "
                    f"{batch_saved} questions saved this batch, "
                    f"{db_inserted} saved this round so far"
                )
            # Overwrite parser_output with only remaining items that need further verification
            request.parser_output = remaining_items
            db_saved_total = db_saved_total_before + db_inserted
            self.logger.agent_node(
                f"Teacher round {round_now} summary: "
                f"{db_inserted} questions saved this round, "
                f"{db_saved_total} total questions saved to database so far, "
                f"{len(remaining_items)} remaining"
            )
            return {
                "request": request,
                "phase": "verify",
                "is_agreed": is_agreed,
                "round": round_now + 1,
                "max_round": max_round,
                "confidence": confidence,
                "solutions": solutions,
                "teacher_feedback": feedback,
                "discrimination_a": discrimination_a,
                "difficulty_b": difficulty_b,
                "topic_tags": [
                    topic_tags_by_id.get(item.get("id") or item.get("question_id"), [])
                    for item in item_list
                ],
                "db_saved_total": db_saved_total,
            }

        if intent == Intent.ASK_HINT.value:
            question = await self.get_data("masterthpt", "questions", {"question_id": request.question_id})
            question = question[0] if question else None
            
            content = question.get("content") if question else "N/A"
            options = question.get("options") if question else []
            correct_answer = question.get("correct_answer") if question else None
            content += "\nCác lựa chọn:\n" + "\n".join(options) + f"\nĐáp án đúng: {correct_answer}" if options else ""

            student_answer = request.student_answers[-1].student_answer if request.student_answers else None
            student_message = request.student_message if request.student_message else ""

            prompt = teacher_hint_prompt(content, student_answer, student_message)
            # print(prompt)
            response = await self._llm_with_single_output.ainvoke(
                self.build_messages(prompt)
            )
            self.logger.agent_node(f"Hint response: {response}")
            hint_feedback_message = AIMessage(
                content=json.dumps(response.model_dump(), ensure_ascii=False)
            )
            return {
                "request": request,
                "questions": state.get("questions", []),
                "student_answers": state.get("student_answers", []),
                "phase": "END",
                "round": state.get("round", 0),
                "confidence": state.get("confidence", []),
                "is_agreed": state.get("is_agreed", []),
                "teacher_feedback": [hint_feedback_message]
            }

        if intent == Intent.REVIEW_MISTAKE.value:
            question = await self.get_data("masterthpt", "questions", {"question_id": request.question_id})
            question = question[0] if question else None

            content = question.get("content") if question else "N/A"
            options = question.get("options") if question else []
            correct_answer = question.get("correct_answer") if question else None
            content += "\nCác lựa chọn:\n" + "\n".join(options) + f"\nĐáp án đúng: {correct_answer}" if options else ""

            student_answer = request.student_answers[-1].student_answer if request.student_answers else None
            student_message = request.student_message if request.student_message else ""

            prompt = teacher_review_mistake_prompt(content, student_answer, student_message)
            # print(prompt)
            response = await self._llm_with_single_output.ainvoke(
                self.build_messages(prompt)
            )
            self.logger.agent_node(f"Review mistake response: {response}")
            review_feedback_message = AIMessage(
                content=json.dumps(response.model_dump(), ensure_ascii=False)
            )
            return {
                "request": request,
                "questions": state.get("questions", []),
                "phase": "verify",
                "round": round_now + 1,
                "max_round": max_round,
                "confidence": [response.confidence],
                "is_agreed": [response.agree],
                "student_answers": [
                    StudentAnswer(
                        question_id=request.question_id,
                        student_answer=student_answer,
                    )
                ],
                "teacher_feedback": [review_feedback_message]
            }


    async def teacher(self, state: AgentState) -> AgentState:
        self.logger.agent_node("Teacher debate started")
        next_state = await self._run_batch(state)
        self.logger.agent_node("Teacher debate completed")
        return next_state
    
    async def run(self, input: str) -> str:
        return "Use run_draft() or run_debate() instead."
