from __future__ import annotations

from typing import Optional, Literal
from typing_extensions import TypedDict
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from master.agents import BaseAgent
from master.agents.common.message import (
    StudentAnswer, Intent, MessageRequest, ExamQuestion,
)
from master.agents.common import tools
from master.agents.common.tools import ToolsRegistry
from master.agents.common.llm_client import LLMClient

import asyncio

load_dotenv(override=True)


# ── Internal models ────────────────────────────────────────────────────────────

class DraftResult(BaseModel):
    """Kết quả Teacher tạo ra ở vòng đầu, tuỳ intent."""
    question_id: Optional[str] = None
    # GRADE / VIEW_ANALYSIS
    is_correct: Optional[bool] = None
    score: Optional[float] = None
    # ASK_HINT / REVIEW_MISTAKE
    response_text: Optional[str] = None
    # PREPROCESS
    parsed_questions: Optional[list[ExamQuestion]] = None
    # Mọi intent
    reasoning: str = ""
    feedback: str = ""        # Gửi cho Verifier


class DebateResult(BaseModel):
    """Phản biện của Teacher sau khi nghe Verifier."""
    question_id: Optional[str] = None
    teacher_rebuttal: str
    final_response: str        # Kết quả cuối: text, JSON, ...
    final_score: Optional[float] = None
    accepted_verifier: bool = False


class Output(BaseModel):
    """Đơn vị xử lý xuyên suốt pipeline — 1 câu hỏi hoặc 1 đơn vị xử lý."""
    student_ans: Optional[StudentAnswer] = None   # None với PREPROCESS / ASK_HINT
    draft_result: Optional[DraftResult] = None
    verifier_feedback: list[str] = Field(default_factory=list)
    debate_result: Optional[DebateResult] = None


# ── AgentState ─────────────────────────────────────────────────────────────────

class AgentState(TypedDict):
    outputs: list[Output]
    round: int
    max_round: int
    phase: Literal["draft", "debate"]
    intent: Intent
    exam_id: Optional[str]
    student_id: Optional[str]
    raw_request: MessageRequest


# Backward-compat alias cho VerifierAgent
DebateState = AgentState


# ── TeacherAgent ───────────────────────────────────────────────────────────────

class TeacherAgent(BaseAgent, ToolRegistry):
    def __init__(self):
        super().__init__(agent_role="teacher")
        self.memory = MemorySaver()
        self.graph  = None

    async def setup(self):
        await self.setup_tools(LLMClient.chat_model())
        self.graph = self._build_graph()

    def _build_graph(self):
        builder = StateGraph(AgentState)
        builder.add_node("draft",  self._draft_batch)
        builder.add_node("debate", self._debate_batch)
        builder.add_conditional_edges(
            START,
            lambda s: s["phase"],
            {"draft": "draft", "debate": "debate"},
        )
        builder.add_edge("draft",  END)
        builder.add_edge("debate", END)
        return builder.compile(checkpointer=self.memory)

    # ── Build initial AgentState from MessageRequest ───────────────────────────

    def _build_state(self, request: MessageRequest, max_round: int) -> AgentState:
        """
        Mọi intent đều được đưa vào 1 state duy nhất.
        - ASK_HINT / PREPROCESS: 1 Output duy nhất, không có student_ans.
        - REVIEW_MISTAKE / VIEW_ANALYSIS / EXAM_PRACTICE: 1 Output mỗi StudentAnswer.
        """
        match request.intent:
            case Intent.ASK_HINT:
                outputs = [Output()]          # 1 đơn vị, không có student_ans

            case Intent.PREPROCESS:
                outputs = [Output()]          # 1 đơn vị cho cả block câu hỏi

            case _:
                # REVIEW_MISTAKE, VIEW_ANALYSIS, EXAM_PRACTICE
                outputs = [
                    Output(student_ans=sa)
                    for sa in (request.student_answers or [])
                ]

        return AgentState(
            outputs     = outputs,
            round       = 0,
            max_round   = max_round,
            phase       = "draft",
            intent      = request.intent,
            exam_id     = request.exam_id,
            student_id  = request.student_id,
            raw_request = request,
        )

    # ── Draft Phase ────────────────────────────────────────────────────────────

    async def _draft_single(self, output: Output, state: AgentState) -> Output:
        req    = state["raw_request"]
        intent = state["intent"]

        match intent:
            case Intent.ASK_HINT:
                question = await tools.get_data(
                    "masterthpt", "questions", query={"id": req.question_id}
                )
                prompt = f"""Bạn là giáo viên tạo gợi ý cho học sinh.
Câu hỏi    : {question}
Thắc mắc HS: {req.student_message or "Không có"}

Tạo gợi ý giúp học sinh tự tìm ra đáp án, KHÔNG tiết lộ đáp án trực tiếp.
Ghi rõ reasoning (lý luận) và feedback (nhận xét gửi Verifier)."""
                result: DraftResult = await self._run_with_tools(prompt, DraftResult)
                result.question_id = req.question_id

            case Intent.REVIEW_MISTAKE:
                sa       = output.student_ans
                question = await tools.get_data(
                    "masterthpt", "questions", query={"id": sa.question_id}
                )
                prompt = f"""Bạn là giáo viên phân tích lỗi sai của học sinh.
Câu hỏi    : {question}
Trả lời HS : {sa.student_answer}

Phân tích nguyên nhân sai, phân loại lỗi, đưa ra hướng khắc phục.
Ghi rõ reasoning và feedback (nhận xét gửi Verifier).
question_id phải là: {sa.question_id}"""
                result: DraftResult = await self._run_with_tools(prompt, DraftResult)
                result.question_id = sa.question_id

            case Intent.PREPROCESS:
                prompt = f"""Bạn là giáo viên parse đề thi thành cấu trúc ExamQuestion.
Nội dung thô: {req.parser_output}

Parse thành list ExamQuestion chuẩn JSON, ghi vào parsed_questions.
Ghi rõ reasoning và feedback (nhận xét gửi Verifier)."""
                result: DraftResult = await self._run_with_tools(prompt, DraftResult)

            case _:
                # VIEW_ANALYSIS / EXAM_PRACTICE — chấm điểm câu hỏi
                sa       = output.student_ans
                question = await tools.get_data(
                    "masterthpt", "questions", query={"id": sa.question_id}
                )
                prompt = f"""Bạn là giáo viên chấm thi.
Câu hỏi    : {question}
Trả lời HS : {sa.student_answer}

Chấm điểm, đưa ra nhận xét để Verifier kiểm tra.
question_id phải là: {sa.question_id}"""
                result: DraftResult = await self._run_with_tools(prompt, DraftResult)
                result.question_id = sa.question_id

        return output.model_copy(update={"draft_result": result})

    async def _draft_batch(self, state: AgentState) -> AgentState:
        updated = await asyncio.gather(
            *[self._draft_single(o, state) for o in state["outputs"]]
        )
        return {**state, "outputs": list(updated)}

    # ── Debate Phase ───────────────────────────────────────────────────────────

    async def _debate_single(self, output: Output, state: AgentState) -> Output:
        req    = state["raw_request"]
        intent = state["intent"]
        draft  = output.draft_result

        match intent:
            case Intent.ASK_HINT:
                prompt = f"""Verifier phản biện gợi ý của bạn. Hãy bảo vệ hoặc cải thiện.
Gợi ý ban đầu    : {draft.response_text if draft else "Chưa có"}
Feedback Verifier: {output.verifier_feedback}

Trả về final_response là gợi ý đã cải thiện."""

            case Intent.REVIEW_MISTAKE:
                sa = output.student_ans
                prompt = f"""Verifier phản biện phân tích lỗi của bạn. Hãy bảo vệ hoặc cải thiện.
Phân tích ban đầu: {draft.response_text if draft else "Chưa có"}
Feedback Verifier: {output.verifier_feedback}
question_id phải là: {sa.question_id}

Trả về final_response là phân tích đã cải thiện."""

            case Intent.PREPROCESS:
                prompt = f"""Verifier phản biện câu hỏi bạn parse. Hãy sửa lại nếu cần.
Parse ban đầu    : {draft.parsed_questions if draft else "Chưa có"}
Feedback Verifier: {output.verifier_feedback}

Trả về final_response là JSON list ExamQuestion đã sửa."""

            case _:
                sa = output.student_ans
                prompt = f"""Verifier phản biện kết quả chấm. Hãy bảo vệ hoặc cải thiện.
Chấm ban đầu     : {draft.model_dump() if draft else "Chưa có"}
Feedback Verifier: {output.verifier_feedback}
question_id phải là: {sa.question_id}

Trả về final_response và final_score đã cập nhật."""

        result: DebateResult = await self._run_with_tools(prompt, DebateResult)
        if output.student_ans:
            result.question_id = output.student_ans.question_id
        return output.model_copy(update={"debate_result": result})

    async def _debate_batch(self, state: AgentState) -> AgentState:
        updated = await asyncio.gather(
            *[self._debate_single(o, state) for o in state["outputs"]]
        )
        return {**state, "outputs": list(updated), "round": state["round"] + 1}

    # ── Public API ─────────────────────────────────────────────────────────────

    async def run_draft(
        self,
        request: MessageRequest,
        max_round: int = 3,
        thread_id: str = "default",
    ) -> AgentState:
        """MessageRequest → AgentState sau draft phase."""
        state  = self._build_state(request, max_round)
        config = {"configurable": {"thread_id": thread_id}}
        return await self.graph.ainvoke(state, config=config)

    async def run_debate(
        self,
        state: AgentState,
        thread_id: str = "default",
    ) -> AgentState:
        """AgentState có verifier_feedback → AgentState sau debate phase."""
        config = {"configurable": {"thread_id": thread_id}}
        return await self.graph.ainvoke({**state, "phase": "debate"}, config=config)

    async def run(self, input: str) -> str:
        return "Use run_draft(MessageRequest) or run_debate(AgentState)."