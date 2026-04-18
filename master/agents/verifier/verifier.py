from typing import Optional, Annotated, Any, List
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.message import add_messages
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
        last_feedback = state["verifier_feedback"][-1] if state["verifier_feedback"] else None
        request = state["request"]
        intent = request.intent

        if hasattr(last_feedback, "tool_calls") and last_feedback.tool_calls:
            return "tools"
        if state["phase"] == "END":
            return "END"
        if state["phase"] == "teacher":
            if state["round"] >= state["max_round"] or (state["confidence"] and state["is_agreed"] and (state["confidence"][0] >= 0.9 or state["is_agreed"][0] and intent == Intent.REVIEW_MISTAKE.value)):
                return "END"
        return "teacher"

    def format_conversation(self, state: AgentState) -> str:
        conversation = "Conversation history:\n\n"
        for i, feedback in enumerate(state["teacher_feedback"]):
            conversation += f"Round {i+1}:\n"
            conversation += f"Teacher feedback: {feedback}\n"
            if i < len(state["verifier_feedback"]):
                conversation += f"Verifier feedback: {state['verifier_feedback'][i]}\n"
            conversation += "\n"
        return conversation


    # Hàm này dùng để chấm điểm theo lô (batch) các câu hỏi, trả về feedback cho từng câu hỏi và confidence của Verifier về độ chính xác của Teacher
    async def _run_batch(self, state: AgentState) -> AgentState:
        request = state["request"]
        intent = request.intent

        is_agreed = []
        solutions = []
        confidence = []
        feedback = []
        item_list = request.parser_output
        id_to_index = {item["id"]: idx for idx, item in enumerate(item_list)} if item_list else {}
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
                batch_map = {item["id"]: item for item in batch}
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

                    data = {
                        "id": item["id"],
                        "question_index": item["question_index"],
                        "type": item.get("type"),
                        "content": item.get("content"),
                        "options": item.get("options"),
                        "correct_answer": correct_answer,
                        "has_image": item.get("has_image"),
                        "image_url": item.get("image_url"),
                        "discrimination_a": discrimination_a,
                        "difficulty_b": difficulty_b,
                    }

                    await self.insert_data("masterthpt", "questions", [data])
                    self.logger.agent_node(f"Skip verify preprocess payload: {data}")
            
            need_verify = [item for item in batch if item["id"] not in skip_verify]
            if not need_verify:
                continue

            batch_input_json = json.dumps(need_verify, ensure_ascii=False, indent=2)
            prompt = verifier_prompt(batch_input_json)
            # prompt += self.format_conversation(state)
            
            responses: EvaluateBatch = await self._llm_with_output.ainvoke(prompt)

            if intent == Intent.PREPROCESS.value and state["round"] >= state["max_round"] and need_verify:
                need_verify_by_id = {item["id"]: item for item in need_verify}
                for response in responses.results:
                    item = need_verify_by_id.get(response.question_id)
                    if not item:
                        continue

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
                    }
                    await self.insert_data("masterthpt", "questions", [data])
                    self.logger.agent_node(f"Finalize by verifier payload: {data}")
            
            # Gửi feedback cho từng câu hỏi trong batch để phản hồi cho học sinh (có thể dùng trong intent "REVIEW_MISTAKE" hoặc PREPROCESS đều được)
            for ids in skip_verify:
                state.setdefault("response", []).append(MessageResponse(
                    student_id=request.student_id,
                    exam_id=request.exam_id,
                    question_id=ids,
                    feedback=f"Câu trả lời đúng là {state['teacher_feedback'][-1]}"
                ))

            # Cần thảo luận thêm các câu chưa chắc chắn để đưa ra quyết định cuối cùng
            is_agreed.extend([response.agree for response in responses.results])
            solutions.extend([
                Solution(question_id=response.question_id, solution=response.correct_answer)
                for response in responses.results
            ])
            confidence.extend([response.confidence for response in responses.results])
            feedback.extend([
                f"Ở câu {response.question_id}: {response.feedback} vì {response.reasoning}"
                for response in responses.results
            ])
            self.logger.agent_node(f"Preprocess batch {i//BATCH_SIZE + 1} result: {responses}")
        return {
            "request": request,
            "phase": "teacher",
            "is_agreed": is_agreed,
            "round": state["round"] + 1,
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