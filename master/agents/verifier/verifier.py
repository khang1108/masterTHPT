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
from master.agents.common.prompt import verifier_prompt, verifier_system_prompt

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
        self.system_prompt = verifier_system_prompt()
        self._llm               = None
        self._llm_with_output   = None
        self._memory            = MemorySaver()
        self.graph              = None

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
            max_tokens=8192,
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
        remaining_items = []  # Collect items that still need verification
        db_inserted = 0  # Track total DB inserts this round
        state_confidence = state.get("confidence", []) or []
        state_is_agreed = state.get("is_agreed", []) or []
        state_discrimination_a = state.get("discrimination_a", []) or []
        state_difficulty_b = state.get("difficulty_b", []) or []
        state_solutions = state.get("solutions", []) or []
        solution_by_id = {}
        for solution in state_solutions:
            if hasattr(solution, "question_id") and hasattr(solution, "solution"):
                solution_by_id[solution.question_id] = solution.solution
            elif isinstance(solution, dict):
                question_id = solution.get("question_id")
                if question_id:
                    solution_by_id[question_id] = solution.get("solution")

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
                    question_type = (item.get("type") or "").strip().lower()
                    normalized_correct_answer = None

                    if question_type == "true_false":
                        expected_count = len(item.get("options") or [])
                        answer_text = str(correct_answer or "").strip().upper()
                        tokens = [token.strip() for token in answer_text.split(",") if token.strip()]
                        if tokens and all(token in {"T", "F"} for token in tokens):
                            if expected_count == 0 or len(tokens) == expected_count:
                                normalized_correct_answer = ", ".join(tokens)
                    elif question_type == "multiple_choice":
                        answer_text = str(correct_answer or "").strip().upper()
                        if answer_text in {"A", "B", "C", "D"}:
                            normalized_correct_answer = answer_text
                    elif question_type in {"short_ans", "short_answer"}:
                        answer_text = str(correct_answer or "").strip()
                        if re.fullmatch(r"[+-]?(?:\d+(?:\.\d+)?|\.\d+)", answer_text):
                            normalized_correct_answer = answer_text
                    else:
                        normalized_correct_answer = correct_answer

                    data = {
                        "question_id": item.get("id") or item.get("question_id"),
                        "question_index": item["question_index"],
                        "type": item.get("type"),
                        "content": item.get("content"),
                        "options": item.get("options"),
                        "correct_answer": normalized_correct_answer,
                        "has_image": item.get("has_image"),
                        "image_url": item.get("image_url"),
                        "discrimination_a": discrimination_a,
                        "difficulty_b": difficulty_b,
                    }

                    await self.insert_data("masterthpt", "questions", [data])
                    db_inserted += 1
                self.logger.agent_node(f"Verifier skip verify: {len(skip_verify)} items inserted")
            
            need_verify = [item for item in batch if (item.get("id") or item.get("question_id")) not in skip_verify]
            remaining_items.extend(need_verify)
            if not need_verify:
                continue

            batch_input_json = json.dumps(need_verify, ensure_ascii=False, indent=2)
            prompt = verifier_prompt(batch_input_json)
            prompt += self.format_conversation(state)
            
            responses: EvaluateBatch = await self._llm_with_output.ainvoke(prompt)

            response_by_id = {r.question_id: r for r in responses.results}
            missing = [item for item in need_verify if (item.get("id") or item.get("question_id")) not in response_by_id]
            retry_count = 0
            while missing and retry_count < 2:
                retry_count += 1
                self.logger.agent_node(f"Verifier retry {retry_count}: {len(missing)} missing items")
                retry_json = json.dumps(missing, ensure_ascii=False, indent=2)
                retry_prompt = verifier_prompt(retry_json)
                retry_prompt += self.format_conversation(state)
                retry_responses: EvaluateBatch = await self._llm_with_output.ainvoke(retry_prompt)
                for r in retry_responses.results:
                    response_by_id[r.question_id] = r
                missing = [item for item in need_verify if (item.get("id") or item.get("question_id")) not in response_by_id]

            if intent == Intent.PREPROCESS.value and round_now >= max_round and need_verify:
                for item in need_verify:
                    item_id = item.get("id") or item.get("question_id")
                    response = response_by_id.get(item_id)
                    item_index = id_to_index.get(item_id)

                    raw_correct_answer = response.correct_answer if response else solution_by_id.get(item_id)
                    question_type = (item.get("type") or "").strip().lower()
                    normalized_correct_answer = None

                    if question_type == "true_false":
                        expected_count = len(item.get("options") or [])
                        answer_text = str(raw_correct_answer or "").strip().upper()
                        tokens = [token.strip() for token in answer_text.split(",") if token.strip()]
                        if tokens and all(token in {"T", "F"} for token in tokens):
                            if expected_count == 0 or len(tokens) == expected_count:
                                normalized_correct_answer = ", ".join(tokens)
                    elif question_type == "multiple_choice":
                        answer_text = str(raw_correct_answer or "").strip().upper()
                        if answer_text in {"A", "B", "C", "D"}:
                            normalized_correct_answer = answer_text
                    elif question_type in {"short_ans", "short_answer"}:
                        answer_text = str(raw_correct_answer or "").strip()
                        if re.fullmatch(r"[+-]?(?:\d+(?:\.\d+)?|\.\d+)", answer_text):
                            normalized_correct_answer = answer_text
                    else:
                        normalized_correct_answer = raw_correct_answer

                    disc_a = response.discrimination_a if response else (
                        state_discrimination_a[item_index] if item_index is not None and item_index < len(state_discrimination_a) else None
                    )
                    diff_b = response.difficulty_b if response else (
                        state_difficulty_b[item_index] if item_index is not None and item_index < len(state_difficulty_b) else None
                    )

                    data = {
                        "question_id": item_id,
                        "question_index": item.get("question_index"),
                        "type": item.get("type"),
                        "content": item.get("content"),
                        "options": item.get("options"),
                        "correct_answer": normalized_correct_answer,
                        "has_image": item.get("has_image"),
                        "image_url": item.get("image_url"),
                        "discrimination_a": disc_a,
                        "difficulty_b": diff_b,
                    }
                    await self.insert_data("masterthpt", "questions", [data])
                    db_inserted += 1
                self.logger.agent_node(f"Verifier finalize: {len(need_verify)} items force-inserted")
            
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
            for item in need_verify:
                item_id = item.get("id") or item.get("question_id")
                r = response_by_id.get(item_id)
                if r:
                    is_agreed.append(r.agree)
                    confidence.append(r.confidence)
                    if r.correct_answer is not None and str(r.correct_answer).strip() != "":
                        solutions.append(
                            Solution(question_id=r.question_id, solution=str(r.correct_answer).strip())
                        )
                    feedback.append(
                        AIMessage(content=f"Ở câu {r.question_id}: {r.feedback} vì {r.reasoning}")
                    )
                else:
                    self.logger.agent_node(f"Verifier: no response for {item_id} after retries")
                    is_agreed.append(False)
                    confidence.append(0.0)
                    feedback.append(
                        AIMessage(content=f"Ở câu {item_id}: Không có phản hồi từ Verifier LLM")
                    )
            self.logger.agent_node(f"Preprocess batch {i//BATCH_SIZE + 1} result: {len(response_by_id)}/{len(need_verify)} responses")
        # Overwrite parser_output with only remaining items that need further verification
        request.parser_output = remaining_items
        self.logger.agent_node(f"Verifier round {round_now} summary: {db_inserted} saved to DB, {len(remaining_items)} remaining")
        return {
            "request": request,
            "phase": "teacher",
            "is_agreed": is_agreed,
            "round": round_now + 1,
            "max_round": max_round,
            "confidence": confidence,
            "solutions": solutions,
            "verifier_feedback": feedback
        }

    async def verifier(self, state: AgentState) -> AgentState:
        self.logger.agent_node("Verifier debate started")
        next_state = await self._run_batch(state)
        self.logger.agent_node("Verifier debate completed")
        return next_state
    
    async def run(self, input: str) -> str:
        return "Use run_draft() or run_debate() instead."
    
# if __name__ == "__main__":
#     from master.agents.teacher.teacher import TeacherAgent
#     teacher = TeacherAgent()
#     verifier = VerifierAgent()

#     request = MessageRequest(
#         intent=Intent.PREPROCESS.value,
#         student_id="student_123",
#         student_answers=[StudentAnswer(question_id='07931d51-d61b-5a58-bb3b-351a8edccbcd', student_answer="B")],
#         question_id='07931d51-d61b-5a58-bb3b-351a8edccbcd',
#         parser_output=[{
#             "id": '07931d51-d61b-5a58-bb3b-351a8edccbcd',
#             "type": 'multiple_choice',
#             "content": 'Cho hình nón (N) có đường cao $SO = h$ và bán kính đáy bằng $r$, gọi M là điểm trên đoạn SO, đặt $OM = x,\\;0 < x < h$. Gọi (C) là thiết diện của mặt phẳng $(\\alpha)$ vuông góc với SO tại M, với hình nón (N). Tìm $x$ để thể tích khối nón đỉnh O đáy là (C) lớn nhất.',
#             "options": [
#                 'A.$\\frac{h}{3}$',
#                 'B.$\\frac{h\\sqrt{2}}{2}.$',
#                 'C.$\\frac{h}{2}.$',
#                 'D.$\\frac{h\\sqrt{3}}{2}.$'
#             ],
#         }]
#     )

#     state= {
#         "request": request,
#         "phase": "draft",
#         "round": 0,
#         "max_round": 3,
#     }

#     asyncio.run(teacher.setup())
#     asyncio.run(verifier.setup())

#     result = asyncio.run(teacher._run_batch(state))
#     try:
#         print(json.dumps(result, ensure_ascii=True, default=str))
#     except (BrokenPipeError, ValueError):
#         pass

#     verifier.logger.agent_node("Starting verifier with teacher's output")
#     result = asyncio.run(verifier._run_batch(result))
#     try:
#         print(json.dumps(result, ensure_ascii=True, default=str))
#     except (BrokenPipeError, ValueError):
#         pass


    