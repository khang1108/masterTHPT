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
    discrimination_a: float = Field(description="Độ phân biệt của câu hỏi để đánh giá học sinh giỏi hay yếu, giá trị từ 0 đến 1, càng cao càng phân biệt tốt.")
    difficulty_b: float = Field(description="Độ khó của câu hỏi, giá trị từ 0 đến 1, càng cao càng khó.")

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
            model="gpt-oss-120b",
            max_tokens=5000,
            temperature=0.7,
        )
        await self.setup_tools(llm)
        self._llm_with_single_output = self._llm.with_structured_output(Evaluate)
        self._llm_with_batch_output = self._llm.with_structured_output(EvaluateBatch)
        self.logger.agent_node("Teacher setup completed")

    def teacher_router(self, state: AgentState) -> str:
        teacher_feedback = state.get("teacher_feedback") or []
        last_feedback = teacher_feedback[-1] if teacher_feedback else None
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
        if state["phase"] == "verify":
            # PREPROCESS should always go through Verifier; Verifier decides when to stop.
            if intent == Intent.PREPROCESS.value:
                return "verify"
            if round_now >= max_round or (confidence and (confidence[0] >= 0.9 or (is_agreed and is_agreed[0] and intent == Intent.REVIEW_MISTAKE.value))):
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
            
            item_list = request.parser_output or []
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
                skip_verify = [
                    question_id
                    for question_id in [item["id"] for item in batch]
                    if (
                        (id_to_index.get(question_id) is not None and id_to_index[question_id] < len(state_confidence) and state_confidence[id_to_index[question_id]] >= 0.9)
                        or (id_to_index.get(question_id) is not None and id_to_index[question_id] < len(state_is_agreed) and state_is_agreed[id_to_index[question_id]])
                    )
                ]

                if skip_verify:
                    batch_map = {item["id"]: item for item in batch}
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

                        data = {
                            "id": item["id"],
                            "question_index": item["question_index"],
                            "type": item.get("type"),
                            "content": item.get("content"),
                            "options": item.get("options"),
                            "correct_answer": correct_answer_value,
                            "has_image": item.get("has_image"),
                            "image_url": item.get("image_url"),
                            "discrimination_a": discrimination_a_value,
                            "difficulty_b": difficulty_b_value,
                        }

                        await self.insert_data("masterthpt", "questions", [data])
                        self.logger.agent_node(f"Teacher skip verify preprocess payload: {data}")

                need_verify = [item for item in batch if item["id"] not in skip_verify]
                if not need_verify:
                    continue

                batch_input_json = json.dumps(need_verify, ensure_ascii=False, indent=2)
                prompt = teacher_preprocess_prompt(batch_input_json)
                responses: EvaluateBatch = await self._llm_with_batch_output.ainvoke(prompt)

                is_agreed.extend([response.agree for response in responses.results])
                solutions.extend([
                    Solution(question_id=response.question_id, solution=response.correct_answer)
                    for response in responses.results
                ])
                confidence.extend([response.confidence for response in responses.results])
                discrimination_a.extend([response.discrimination_a for response in responses.results])
                difficulty_b.extend([response.difficulty_b for response in responses.results])
                feedback.extend([
                    f"Ở câu {response.question_id}: {response.feedback} vì {response.reasoning}"
                    for response in responses.results
                ])
                self.logger.agent_node(f"Preprocess batch {i//BATCH_SIZE + 1} result: {responses}")
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
            }

        if intent == Intent.ASK_HINT.value:
            question = await self.get_data("masterthpt", "questions", {"id": request.question_id})
            question = question[0] if question else None
            content = question.get("content") if question else ""
            options = question.get("options") if question else []
            content += "\nOptions:\n" + "\n".join(options) if options else ""

            student_answer = request.student_answers[-1].student_answer if request.student_answers else None
            student_message = request.student_message if request.student_message else ""

            prompt = teacher_hint_prompt(content, student_answer, student_message)
            print(prompt)
            response = await self._llm.ainvoke(prompt)
            self.logger.agent_node(f"Hint response: {response}")
            return {
                "request": request,
                "phase": "END",
                "teacher_feedback": [response]
            }

        if intent == Intent.REVIEW_MISTAKE.value:
            question = await self.get_data("masterthpt", "questions", {"id": request.question_id})
            question = question[0] if question else None
            content = question.get("content") if question else ""
            options = question.get("options") if question else []
            content += "\nOptions:\n" + "\n".join(options) if options else ""
                
            student_answer = request.student_answers[-1].student_answer if request.student_answers else None
            student_message = request.student_message if request.student_message else ""

            prompt = teacher_review_mistake_prompt(content, student_answer, student_message)
            print(prompt)
            response = await self._llm_with_single_output.ainvoke(prompt)
            self.logger.agent_node(f"Review mistake response: {response}")
            return {
                "request": request,
                "phase": "verify",
                "round": round_now + 1,
                "max_round": max_round,
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
        intent=Intent.REVIEW_MISTAKE.value,
        student_id="student_123",
        student_answers=[StudentAnswer(question_id='c7b9433a-e22e-5f91-9a8e-6e682612f748', student_answer="B")],
        question_id='c7b9433a-e22e-5f91-9a8e-6e682612f748',
        # parser_output=[{
        #     "id": '07931d51-d61b-5a58-bb3b-351a8edccbcd',
        #     "type": 'multiple_choice',
        #     "content": 'Cho hình nón (N) có đường cao $SO = h$ và bán kính đáy bằng $r$, gọi M là điểm trên đoạn SO, đặt $OM = x,\\;0 < x < h$. Gọi (C) là thiết diện của mặt phẳng $(\\alpha)$ vuông góc với SO tại M, với hình nón (N). Tìm $x$ để thể tích khối nón đỉnh O đáy là (C) lớn nhất.',
        #     "options": [
        #         'A.$\\frac{h}{3}$',
        #         'B.$\\frac{h\\sqrt{2}}{2}.$',
        #         'C.$\\frac{h}{2}.$',
        #         'D.$\\frac{h\\sqrt{3}}{2}.$'
        #     ],
        # }]
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


    