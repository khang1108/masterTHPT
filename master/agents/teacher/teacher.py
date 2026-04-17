from typing import Optional, Annotated, Any, List
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from master.agents import BaseAgent
from master.agents.common.state import AgentState
from master.common.message import Solution
from master.agents.common.message import MessageRequest, StudentAnswer, Intent
from master.agents.common.tools import ToolsRegistry
from master.agents.common.llm_client import LLMClient
from master.agents.common.prompt import (
    teacher_preprocess_prompt,
    teacher_hint_prompt,
    teacher_review_mistake_prompt,
)

import json
import os
import asyncio

load_dotenv(override=True)
BATCH_SIZE = 5

# ── Pydantic Models ────────────────────────────────────────────────────────────

class Evaluate(BaseModel):
    """Kết quả chấm nháp của Teacher."""
    question_id: str
    agree: bool = Field(description="Teacher có đồng ý với feedback của Verifier không? Nếu feedback của Verifier để trống thì điền false.")
    confidence: float = 0.5
    correct_answer: str = Field(description="Đáp án đúng A, B, C, D. Nếu không xác định được đáp án đúng thì để trống.")
    reasoning: str =  Field(description="Giải thích ngắn gọn về lý do đồng ý hay không đồng ý với đáp án của học sinh, hoặc giải thích cách giải nếu đang ở chế độ PREPROCESS.")         
    feedback: str = Field(description="Phản hồi cụ thể cho học sinh, có thể là gợi ý để cải thiện hoặc lời khen nếu đáp án đúng. Phản hồi phải rõ ràng, thân thiện và mang tính xây dựng.")


class EvaluateBatch(BaseModel):
    results: list[Evaluate]


# ── Teacher Agent ──────────────────────────────────────────────────────────────

class TeacherAgent(ToolsRegistry, BaseAgent):
    def __init__(self):
        super().__init__(agent_role="Teacher")
        self._llm        = None
        self._llm_with_single_output = None
        self._llm_with_batch_output = None
        self._memory     = MemorySaver()
        self.graph       = None

    # ── Setup ──────────────────────────────────────────────────────────────────

    async def setup(self):
        self.logger.agent_node("Teacher setup started")
        llm = LLMClient.chat_model(
            provider="openai_compatible",
            base_url=os.getenv("FPT_BASE_URL"),
            api_key=os.getenv("FPT_API_KEY"),
            model="gemma-4-31B-it",
            temperature=0.7,
        )
        await self.setup_tools(llm)
        self._llm_with_single_output = self._llm.with_structured_output(Evaluate)
        self._llm_with_batch_output = self._llm.with_structured_output(EvaluateBatch)
        self.logger.agent_node("Teacher setup completed")

    def teacher_router(self, state: AgentState) -> str:
        last_feedback = state["teacher_feedback"][-1] if state["teacher_feedback"] else None
        request = state["request"]
        intent = request.intent

        if hasattr(last_feedback, "tool_calls") and last_feedback.tool_calls:
            return "tools"
        if state["phase"] == "END":
            return "END"
        if intent == Intent.REVIEW_MISTAKE.value:
            return "verify" if state["confidence"][0] < 0.9 or not state["is_agreed"] else "END"
        if state["phase"] == "verify":
            if state["round"] >= state["max_round"]:
                return "END"
        return "verify" if state["confidence"][0] < 0.9 else "END"


    async def _run_batch(self, state: AgentState) -> AgentState:
        request = state["request"]
        intent = request.intent
        if intent == Intent.PREPROCESS.value:
            is_agreed= []
            solutions = []
            confidence = []
            feedback = []
            
            item_list = request.parser_output
            for i in range(0, len(item_list), BATCH_SIZE):
                batch = item_list[i:i + BATCH_SIZE]
                batch_input_json = json.dumps(batch, ensure_ascii=False, indent=2)


                prompt = teacher_preprocess_prompt(batch_input_json)
                responses: EvaluateBatch = await self._llm_with_batch_output.ainvoke(prompt)

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
                "phase": "verify",
                "is_agreed": is_agreed,
                "round": state["round"] + 1,
                "confidence": confidence,
                "solutions": solutions,
                "teacher_feedback": feedback
            }

        if intent == Intent.ASK_HINT.value:
            question = await self.get_data("masterthpt", "questions", {"id": request.question_id})
            student_answer = request.student_answers[-1].student_answer if request.student_answers else None
            student_message = request.student_message

            prompt = teacher_hint_prompt(question, student_answer, student_message)
            response = await self._llm.ainvoke(prompt)
            self.logger.agent_node(f"Hint response: {response}")
            return {
                "request": request,
                "phase": "END",
                "teacher_feedback": [response]
            }

        if intent == Intent.REVIEW_MISTAKE.value:
            question = await self.get_data("masterthpt", "questions", {"id": request.question_id})
            student_answer = request.student_answers[-1].student_answer if request.student_answers else None
            student_message = request.student_message

            prompt = teacher_review_mistake_prompt(question, student_answer, student_message)
            response = await self._llm_with_single_output.ainvoke(prompt)
            self.logger.agent_node(f"Review mistake response: {response}")
            return {
                "request": request,
                "phase": "verify",
                "round": state["round"] + 1,
                "confidence": [response.confidence],
                "is_agreed": [response.agree],
                "student_answers": StudentAnswer(question_id=request.question_id, student_answer=student_answer),
                "teacher_feedback": [response]
            }


    async def teacher(self, state: AgentState) -> AgentState:
        self.logger.agent_node("Teacher debate started")
        next_state = await self._run_batch(state)
        self.logger.agent_node("Teacher debate completed")
        return next_state
    
    async def run(self, input: str) -> str:
        return "Use run_draft() or run_debate() instead."


if __name__ == "__main__":
    agent = TeacherAgent()
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

    asyncio.run(agent.setup())
    result = asyncio.run(agent._run_batch(state))
    try:
        print(json.dumps(result, ensure_ascii=True, default=str))
    except (BrokenPipeError, ValueError):
        pass


    