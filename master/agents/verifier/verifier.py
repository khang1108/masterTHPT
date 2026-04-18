from typing import Optional, Annotated, Any, List
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.message import add_messages
from langchain_core.messages import AIMessage
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from master.agents import BaseAgent
from master.agents.common.state import AgentState
from master.common.message import Solution
from master.agents.common.message import MessageRequest, MessageResponse, StudentAnswer, Intent
from master.agents.common.tools import ToolsRegistry
from master.agents.teacher.teacher import Evaluate, EvaluateBatch
from master.agents.common.llm_client import LLMClient
from master.agents.common.prompt import verifier_prompt

import asyncio
import json
import re
import uuid
import os

load_dotenv(override=True)
BATCH_SIZE = 3

# ── Verifier Agent ──────────────────────────────────────────────────────────────

class VerifierAgent(ToolsRegistry, BaseAgent):
    def __init__(self):
        super().__init__(agent_role="Verifier")
        self._llm               = None
        self._llm_with_output   = None
        self._memory            = MemorySaver()
        self.graph              = None
        self.system_prompt = """
        Bạn là một AI agent hỗ trợ học sinh THPT Việt Nam trong việc học Toán.

        Bạn phải luôn trả về đúng định dạng output mà hệ thống yêu cầu.
        Ưu tiên cao nhất là:
        1. Đúng schema output
        2. Đúng nội dung toán học.
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

    # ── Setup ──────────────────────────────────────────────────────────────────

    async def setup(self):
        self.logger.agent_node("Verifier setup started")
        llm = LLMClient.chat_model(
            provider="openai_compatible",
            base_url=os.getenv("FPT_BASE_URL"),
            api_key=os.getenv("FPT_API_KEY"),
            model="Qwen3-32B",
            # provider="google_genai",
            # model = "gemini-2.5-flash-lite",
            max_tokens=4096,
            temperature=0.7,
        )
        await self.setup_tools(llm)
        self._llm_with_output = self._llm.with_structured_output(EvaluateBatch)
        self.logger.agent_node("Verifier setup completed")

    def verifier_router(self, state: AgentState) -> str:
        verifier_feedback = state.get("verifier_feedback") or []
        last_feedback = verifier_feedback[-1] if verifier_feedback else None
        request = state["request"]
        intent = request.intent
        round_now = state.get("round", 0)
        max_round = state.get("max_round", 3)
        confidence = state.get("confidence") or []
        is_agreed = state.get("is_agreed") or []

        if hasattr(last_feedback, "tool_calls") and last_feedback.tool_calls:
            return "tools"
        if state["phase"] == "END":
            return "END"
        if state["phase"] == "teacher":
            if round_now >= max_round or (confidence and is_agreed and (confidence[0] >= 0.9 or is_agreed[0] and intent == Intent.REVIEW_MISTAKE.value)):
                return "END"
        return "teacher"

    def format_conversation(self, state: AgentState) -> str:
        teacher_feedback = state.get("teacher_feedback") or []
        verifier_feedback = state.get("verifier_feedback") or []

        if not isinstance(teacher_feedback, list):
            teacher_feedback = [teacher_feedback]
        if not isinstance(verifier_feedback, list):
            verifier_feedback = [verifier_feedback]

        conversation_lines = ["Conversation history:", ""]
        for i, t_feedback in enumerate(teacher_feedback):
            teacher_text = t_feedback.content if hasattr(t_feedback, "content") else str(t_feedback)
            if isinstance(teacher_text, list):
                teacher_text = json.dumps(teacher_text, ensure_ascii=False)
            conversation_lines.append(f"Round {i + 1}:")
            conversation_lines.append(f"Teacher feedback: {teacher_text}")
            if i < len(verifier_feedback):
                verifier_text = verifier_feedback[i].content if hasattr(verifier_feedback[i], "content") else str(verifier_feedback[i])
                if isinstance(verifier_text, list):
                    verifier_text = json.dumps(verifier_text, ensure_ascii=False)
                conversation_lines.append(f"Verifier feedback: {verifier_text}")
            conversation_lines.append("")

        return "\n".join(conversation_lines)


    # Hàm này dùng để chấm điểm theo lô (batch) các câu hỏi, trả về feedback cho từng câu hỏi và confidence của Verifier về độ chính xác của Teacher
    async def _run_batch(self, state: AgentState) -> AgentState:
        request = state["request"]
        intent = request.intent
        round_now = state.get("round", 0)
        max_round = state.get("max_round", 3)

        is_agreed = []
        solutions = []
        confidence = []
        feedback = []
        item_list = request.parser_output or []
        teacher_feedback = state.get("teacher_feedback") or []
        id_to_index = {item["id"]: idx for idx, item in enumerate(item_list)} if item_list else {}
        state_confidence = state.get("confidence", []) or []
        state_is_agreed = state.get("is_agreed", []) or []
        state_discrimination_a = state.get("discrimination_a", []) or []
        state_difficulty_b = state.get("difficulty_b", []) or []
        state_topic_tags = state.get("topic_tags", []) or []
        topic_tags_by_id: dict[str, list[str]] = {}
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
            question_ids = [item["id"] for item in batch]
            
            skip_verify = [
                question_id
                for question_id in question_ids
                if (
                    (id_to_index.get(question_id) is not None and id_to_index[question_id] < len(state_confidence) and state_confidence[id_to_index[question_id]] >= 0.9)
                    or (id_to_index.get(question_id) is not None and id_to_index[question_id] < len(state_is_agreed) and state_is_agreed[id_to_index[question_id]])
                )
            ]
            
            # TODO: CASTING OUTPUT AND INSERT IT TO DATABASE
            if intent == Intent.PREPROCESS.value and skip_verify:
                batch_map = {(item.get("id") or item.get("question_id")): item for item in batch}
                for ids in skip_verify:
                    item = batch_map.get(ids)
                    if not item:
                        continue

                    item_index = id_to_index.get(ids)
                    discrimination_a = (
                        state_discrimination_a[item_index]
                        if item_index is not None and item_index < len(state_discrimination_a)
                        else None
                    )
                    difficulty_b = (
                        state_difficulty_b[item_index]
                        if item_index is not None and item_index < len(state_difficulty_b)
                        else None
                    )
                    correct_answer = solution_by_id.get(ids)
                    topic_tags = topic_tags_by_id.get(ids) or self.trace_question_topics(
                        question_text=item.get("content", ""),
                        options=item.get("options"),
                    )
                    topic_tags_by_id[ids] = topic_tags

                    data = {
                        "question_id": item.get("id") or item.get("question_id"),
                        "question_index": item["question_index"],
                        "type": item.get("type"),
                        "content": item.get("content"),
                        "options": item.get("options"),
                        "correct_answer": correct_answer,
                        "has_image": item.get("has_image"),
                        "image_url": item.get("image_url"),
                        "discrimination_a": discrimination_a,
                        "difficulty_b": difficulty_b,
                        "topic_tags": topic_tags,
                    }

                    await self.insert_data("masterthpt", "questions", [data])
                    self.logger.agent_node(f"Skip verify preprocess payload: {data}")
            
            need_verify = [item for item in batch if (item.get("id") or item.get("question_id")) not in skip_verify]
            if not need_verify:
                continue

            batch_input_json = json.dumps(need_verify, ensure_ascii=False, indent=2)
            prompt = verifier_prompt(batch_input_json)
            prompt += self.format_conversation(state)
            
            responses: EvaluateBatch = await self._llm_with_output.ainvoke(
                self.build_messages(prompt)
            )

            if intent == Intent.PREPROCESS.value and round_now >= max_round and need_verify:
                need_verify_by_id = {item["id"]: item for item in need_verify}
                for response in responses.results:
                    item = need_verify_by_id.get(response.question_id)
                    if not item:
                        continue
                    topic_tags = self.trace_question_topics(
                        question_text=item.get("content", ""),
                        options=item.get("options"),
                        candidate_topics=response.topic_tags,
                    )
                    topic_tags_by_id[response.question_id] = topic_tags

                    data = {
                        "id": item["id"],
                        "question_index": item["question_index"],
                        "type": item.get("type"),
                        "content": item.get("content"),
                        "options": item.get("options"),
                        "correct_answer": response.correct_answer,
                        "has_image": item.get("has_image"),
                        "image_url": item.get("image_url"),
                        "discrimination_a": response.discrimination_a,
                        "difficulty_b": response.difficulty_b,
                        "topic_tags": topic_tags,
                    }
                    await self.insert_data("masterthpt", "questions", [data])
                    self.logger.agent_node(f"Finalize by verifier payload: {data}")
            
            # Gửi feedback cho từng câu hỏi trong batch để phản hồi cho học sinh (có thể dùng trong intent "REVIEW_MISTAKE" hoặc PREPROCESS đều được)
            for ids in skip_verify:
                latest_teacher_feedback = teacher_feedback[-1].content if teacher_feedback and hasattr(teacher_feedback[-1], "content") else (teacher_feedback[-1] if teacher_feedback else "")
                if isinstance(latest_teacher_feedback, list):
                    latest_teacher_feedback = json.dumps(latest_teacher_feedback, ensure_ascii=False)
                state.setdefault("response", []).append(MessageResponse(
                    student_id=request.student_id,
                    exam_id=request.exam_id,
                    question_id=ids,
                    feedback=f"Câu trả lời đúng là {latest_teacher_feedback}"
                ))

            # Cần thảo luận thêm các câu chưa chắc chắn để đưa ra quyết định cuối cùng
            is_agreed.extend([response.agree for response in responses.results])
            solutions.extend([
                Solution(question_id=response.question_id, solution=response.correct_answer)
                for response in responses.results
            ])
            confidence.extend([response.confidence for response in responses.results])
            feedback.extend([
                AIMessage(content=f"Ở câu {response.question_id}: {response.feedback} vì {response.reasoning}")
                for response in responses.results
            ])
            self.logger.agent_node(f"Preprocess batch {i//BATCH_SIZE + 1} result: {responses}")
        return {
            "request": request,
            "phase": "teacher",
            "is_agreed": is_agreed,
            "round": round_now + 1,
            "max_round": max_round,
            "confidence": confidence,
            "solutions": solutions,
            "verifier_feedback": feedback,
            "topic_tags": [
                topic_tags_by_id.get(item.get("id") or item.get("question_id"), [])
                for item in item_list
            ],
        }

    async def verifier(self, state: AgentState) -> AgentState:
        self.logger.agent_node("Verifier debate started")
        next_state = await self._run_batch(state)
        self.logger.agent_node("Verifier debate completed")
        return next_state
    
    async def run(self, input: str) -> str:
        return "Use run_draft() or run_debate() instead."
