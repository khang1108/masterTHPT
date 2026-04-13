from __future__ import annotations

from typing import Optional, Literal, Union
from typing_extensions import TypedDict
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from master.agents import BaseAgent
from master.agents.common import tools
from master.agents.common.tools import ToolsRegistry
from master.agents.common.llm_client import LLMClient
from master.agents.common.message import (
    Intent, MessageRequest, MessageResponse, ExamQuestion,
)
from master.agents.teacher import (
    AgentState, DebateState, Output, DraftResult, DebateResult,
)

import asyncio

load_dotenv(override=True)


# ── Verifier internal models ───────────────────────────────────────────────────

class VerifierVerdict(BaseModel):
    question_id: Optional[str] = None
    agreed: bool
    confidence: float = 1.0
    feedback: list[str] = Field(default_factory=list)
    reasoning: str
    suggested_score: Optional[float] = None


class VerifierState(TypedDict):
    agent_state: AgentState                  # Từ Teacher
    verdicts: list[VerifierVerdict]
    pending_ids: list[str]                   # question_id hoặc ["__single__"]
    satisfied_ids: list[str]
    phase: Literal["verify", "finalize"]


# ── Public output models ───────────────────────────────────────────────────────

class VerifiedQuestion(BaseModel):
    exam_id: str
    question_id: str
    final_score: Optional[float] = None
    is_correct: bool
    reasoning_chain: list[str]
    consensus_note: str


class VerifiedResult(BaseModel):
    exam_id: str
    student_id: Optional[str] = None
    questions: list[VerifiedQuestion]
    total_questions: int
    total_correct: int
    total_score: float


# ── VerifierAgent ──────────────────────────────────────────────────────────────

class VerifierAgent(BaseAgent, ToolRegistry):
    def __init__(self):
        super().__init__(agent_role="verifier")
        self.memory = MemorySaver()
        self.graph  = None

    async def setup(self):
        await self.setup_tools(LLMClient.chat_model())
        self.graph = self._build_graph()

    def _build_graph(self):
        builder = StateGraph(VerifierState)
        builder.add_node("verify",   self._verify_batch)
        builder.add_node("finalize", self._finalize)

        builder.add_conditional_edges(
            START,
            lambda s: s["phase"],
            {"verify": "verify", "finalize": "finalize"},
        )
        builder.add_conditional_edges(
            "verify",
            lambda s: "finalize" if not s["pending_ids"] else "done",
            {"finalize": "finalize", "done": END},
        )
        builder.add_edge("finalize", END)
        return builder.compile(checkpointer=self.memory)

    # ── Key: mỗi Output → 1 VerifierVerdict ───────────────────────────────────

    async def _verify_one(self, output: Output, agent_state: AgentState) -> VerifierVerdict:
        intent  = agent_state["intent"]
        draft   = output.draft_result
        debate  = output.debate_result
        content = (
            debate.final_response if debate
            else (draft.response_text or str(draft.model_dump())) if draft
            else "Chưa có"
        )
        qid = (output.student_ans.question_id if output.student_ans else "__single__")

        match intent:
            case Intent.ASK_HINT:
                req    = agent_state["raw_request"]
                question = await tools.get_data(
                    "masterthpt", "questions", query={"id": req.question_id}
                )
                prompt = f"""Bạn là Verifier kiểm tra gợi ý của Teacher.
Câu hỏi   : {question}
Gợi ý     : {content}
Feedback cũ: {output.verifier_feedback}

Kiểm tra: gợi ý có đúng hướng, không lộ đáp án không?
agreed=True nếu OK, agreed=False + feedback nếu cần sửa."""

            case Intent.REVIEW_MISTAKE:
                sa       = output.student_ans
                question = await tools.get_data(
                    "masterthpt", "questions", query={"id": sa.question_id}
                )
                prompt = f"""Bạn là Verifier kiểm tra phân tích lỗi của Teacher.
Câu hỏi      : {question}
Trả lời HS   : {sa.student_answer}
Phân tích    : {content}
Feedback cũ  : {output.verifier_feedback}

Kiểm tra: phân tích có chính xác, phân loại lỗi đúng không?
agreed=True nếu OK, agreed=False + feedback nếu cần sửa.
question_id phải là: {sa.question_id}"""

            case Intent.PREPROCESS:
                prompt = f"""Bạn là Verifier kiểm tra câu hỏi Teacher đã parse.
Câu hỏi parsed: {content}
Feedback cũ   : {output.verifier_feedback}

Kiểm tra: parse đúng format ExamQuestion, đáp án hợp lý không?
agreed=True nếu OK, agreed=False + feedback nếu cần sửa."""

            case _:
                # VIEW_ANALYSIS / EXAM_PRACTICE — kiểm tra chấm điểm
                sa       = output.student_ans
                question = await tools.get_data(
                    "masterthpt", "questions", query={"id": sa.question_id}
                )
                prompt = f"""Bạn là Verifier kiểm tra kết quả chấm thi của Teacher.
Câu hỏi  : {question}
Trả lời HS: {sa.student_answer}
Kết quả  : {content}
Feedback cũ: {output.verifier_feedback}

agreed=True nếu đồng ý, agreed=False + feedback nếu không.
question_id phải là: {sa.question_id}"""

        verdict: VerifierVerdict = await self._run_with_tools(prompt, VerifierVerdict)
        verdict.question_id = qid
        return verdict

    async def _verify_batch(self, state: VerifierState) -> VerifierState:
        agent_state = state["agent_state"]
        pending_set = set(state["pending_ids"])

        targets = [
            o for o in agent_state["outputs"]
            if (o.student_ans.question_id if o.student_ans else "__single__") in pending_set
        ]

        new_verdicts = list(await asyncio.gather(
            *[self._verify_one(o, agent_state) for o in targets]
        ))

        # Merge verdicts
        verdict_map = {v.question_id: v for v in state["verdicts"]}
        for v in new_verdicts:
            verdict_map[v.question_id] = v

        # Cập nhật verifier_feedback vào outputs
        output_map = {
            (o.student_ans.question_id if o.student_ans else "__single__"): o
            for o in agent_state["outputs"]
        }
        for v in new_verdicts:
            if not v.agreed and v.question_id in output_map:
                output_map[v.question_id] = output_map[v.question_id].model_copy(
                    update={"verifier_feedback": v.feedback}
                )

        all_verdicts  = list(verdict_map.values())
        still_pending = [v.question_id for v in all_verdicts if not v.agreed]
        satisfied     = [v.question_id for v in all_verdicts if v.agreed]

        updated_agent_state = {
            **agent_state,
            "outputs": list(output_map.values()),
            "phase": "debate",
        }

        return {
            **state,
            "agent_state":   updated_agent_state,
            "verdicts":      all_verdicts,
            "pending_ids":   still_pending,
            "satisfied_ids": satisfied,
            "phase":         "verify",
        }

    # ── Finalize: Verifier làm hành động cuối theo intent ─────────────────────

    async def _finalize(self, state: VerifierState) -> VerifierState:
        agent_state = state["agent_state"]
        intent      = agent_state["intent"]
        req         = agent_state["raw_request"]
        outputs     = agent_state["outputs"]

        match intent:
            case Intent.ASK_HINT | Intent.REVIEW_MISTAKE:
                # Lấy final_response từ debate (hoặc draft nếu không có debate)
                o = outputs[0]
                text = (
                    o.debate_result.final_response if o.debate_result
                    else o.draft_result.response_text if o.draft_result
                    else ""
                )
                result = MessageResponse(
                    student_id  = agent_state["student_id"],
                    exam_id     = agent_state["exam_id"],
                    question_id = req.question_id,
                    feedback    = text,
                )

            case Intent.PREPROCESS:
                # Ghi questions vào DB
                o = outputs[0]
                questions_raw = (
                    o.debate_result.final_response if o.debate_result
                    else o.draft_result.parsed_questions if o.draft_result
                    else []
                )
                # Nếu final_response là string JSON, parse lại
                if isinstance(questions_raw, str):
                    import json
                    try:
                        questions_raw = [ExamQuestion(**q) for q in json.loads(questions_raw)]
                    except Exception:
                        questions_raw = []

                if isinstance(questions_raw, list) and questions_raw:
                    for q in questions_raw:
                        q_data = q.model_dump() if isinstance(q, ExamQuestion) else q
                        await tools.insert_data("masterthpt", "questions", q_data)

                result = questions_raw  # list[ExamQuestion]

            case _:
                # VIEW_ANALYSIS / EXAM_PRACTICE — trả VerifiedResult
                verdict_map = {v.question_id: v for v in state["verdicts"]}
                questions: list[VerifiedQuestion] = []
                for o in outputs:
                    qid    = o.student_ans.question_id if o.student_ans else ""
                    draft  = o.draft_result
                    debate = o.debate_result
                    verdict= verdict_map.get(qid)

                    chain = (
                        ([f"[Draft] {draft.reasoning}"] if draft else []) +
                        ([f"[Debate] {debate.teacher_rebuttal}"] if debate else []) +
                        ([f"[Verifier] {verdict.reasoning}"] if verdict else [])
                    )
                    final_score = (
                        debate.final_score if debate and debate.final_score is not None
                        else draft.score if draft
                        else verdict.suggested_score if verdict
                        else None
                    )
                    is_correct = (
                        debate.accepted_verifier if debate
                        else draft.is_correct if draft
                        else False
                    )
                    questions.append(VerifiedQuestion(
                        exam_id         = agent_state["exam_id"] or "",
                        question_id     = qid,
                        final_score     = final_score,
                        is_correct      = is_correct,
                        reasoning_chain = chain,
                        consensus_note  = verdict.reasoning if verdict else "",
                    ))

                result = VerifiedResult(
                    exam_id         = agent_state["exam_id"] or "",
                    student_id      = agent_state["student_id"],
                    questions       = questions,
                    total_questions = len(questions),
                    total_correct   = sum(1 for q in questions if q.is_correct),
                    total_score     = sum(q.final_score or 0.0 for q in questions),
                )

        return {**state, "_final_result": result}

    # ── Public API ─────────────────────────────────────────────────────────────

    async def verify(
        self,
        agent_state: AgentState,
        thread_id: str = "default",
    ) -> tuple[Literal["disagree", "agree"], AgentState | MessageResponse | VerifiedResult | list]:
        """
        Nhận AgentState từ Teacher → verify → finalize nếu agree.

        Returns:
            ("disagree", AgentState) — còn pending, cần Teacher debate tiếp
            ("agree",    result)     — finalize: MessageResponse | VerifiedResult | list[ExamQuestion]
        """
        all_ids = [
            (o.student_ans.question_id if o.student_ans else "__single__")
            for o in agent_state["outputs"]
        ]

        init: VerifierState = {
            "agent_state":   agent_state,
            "verdicts":      [],
            "pending_ids":   all_ids,
            "satisfied_ids": [],
            "phase":         "verify",
        }

        config      = {"configurable": {"thread_id": thread_id}}
        final_state = await self.graph.ainvoke(init, config=config)

        if final_state["pending_ids"]:
            return "disagree", final_state["agent_state"]

        return "agree", final_state["_final_result"]

    async def run(self, input: str) -> str:
        return "Use verify(agent_state) instead."