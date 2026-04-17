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
BATCH_SIZE = 5

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
            # provider="openai_compatible",
            # base_url=os.getenv("FPT_BASE_URL"),
            # api_key=os.getenv("FPT_API_KEY"),
            # model="Qwen3-32B",
            provider="google_genai",
            model = "gemini-2.5-flash-lite",
            max_tokens=8192,
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
            if state["round"] >= state["max_round"] or state["confidence"][0] >= 0.9 or state["is_agreed"][0]:
                return "END"
        return "teacher" if state["confidence"][0] < 0.9 else "END"

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

        is_agreed = []
        solutions = []
        confidence = []
        feedback = []
        item_list = request.parser_output
        for i in range(0, len(item_list), BATCH_SIZE):
            batch = item_list[i:i + BATCH_SIZE]
            question_ids = [item["id"] for item in batch]
            
            skip_verify = [question_id for question_id, confidence in zip(question_ids, state.get("confidence", [])) if confidence >= 0.9]
            skip_verify.extend([question_id for question_id, is_agreed in zip(question_ids, state.get("is_agreed", [])) if is_agreed])
            
            # TODO: CASTING OUTPUT AND INSERT IT TO DATABASE
            
            
            need_verify = [question_id for question_id in question_ids if question_id not in skip_verify]
            batch_input_json = json.dumps(need_verify, ensure_ascii=False, indent=2)
            prompt = verifier_prompt(batch_input_json)
            # prompt += self.format_conversation(state)
            
            responses: EvaluateBatch = await self._llm_with_output.ainvoke(prompt)
            
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
        request = state["request"]
        await self._run_batch(state, request)
        self.logger.agent_node("Verifier debate completed")
        return state
    
    async def run(self, input: str) -> str:
        return "Use run_draft() or run_debate() instead."
    
if __name__ == "__main__":
    from master.agents.teacher.teacher import TeacherAgent
    teacher = TeacherAgent()
    verifier = VerifierAgent()

    request = MessageRequest(
        intent=Intent.PREPROCESS.value,
        student_id="student_123",
        student_answers=[StudentAnswer(question_id='07931d51-d61b-5a58-bb3b-351a8edccbcd', student_answer="B")],
        question_id='07931d51-d61b-5a58-bb3b-351a8edccbcd',
        parser_output=[{
            "id": '07931d51-d61b-5a58-bb3b-351a8edccbcd',
            "type": 'multiple_choice',
            "content": 'Cho hình nón (N) có đường cao $SO = h$ và bán kính đáy bằng $r$, gọi M là điểm trên đoạn SO, đặt $OM = x,\\;0 < x < h$. Gọi (C) là thiết diện của mặt phẳng $(\\alpha)$ vuông góc với SO tại M, với hình nón (N). Tìm $x$ để thể tích khối nón đỉnh O đáy là (C) lớn nhất.',
            "options": [
                'A.$\\frac{h}{3}$',
                'B.$\\frac{h\\sqrt{2}}{2}.$',
                'C.$\\frac{h}{2}.$',
                'D.$\\frac{h\\sqrt{3}}{2}.$'
            ],
        }]
    )

    state= {
        "request": request,
        "phase": "draft",
        "round": 0,
        "max_round": 3,
    }

    asyncio.run(teacher.setup())
    asyncio.run(verifier.setup())

    result = asyncio.run(teacher._run_batch(state))
    try:
        print(json.dumps(result, ensure_ascii=True, default=str))
    except (BrokenPipeError, ValueError):
        pass

    verifier.logger.agent_node("Starting verifier with teacher's output")
    result = asyncio.run(verifier._run_batch(result))
    try:
        print(json.dumps(result, ensure_ascii=True, default=str))
    except (BrokenPipeError, ValueError):
        pass


    