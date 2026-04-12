from typing import List, Optional, Literal
from typing_extensions import TypedDict
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from master.agents import BaseAgent
from master.agents.common import tools
from master.agents.common.tools import ToolRegistry
from master.agents.common.llm_client import LLMClient
# Import từ teacher để dùng chung type
from master.agents.teacher import (
    DebateState, Output, DraftResult, DebateResult, Intent
)

import asyncio

load_dotenv(override=True)


# ── Output khi Verifier đồng ý (gửi cho agent downstream) ─────────────────────

class VerifiedQuestion(BaseModel):
    """Kết quả đã thỏa mãn của 1 câu hỏi sau debate."""
    exam_id: str
    question_id: str
    final_score: Optional[float] = None
    is_correct: bool
    reasoning_chain: list[str]      # Toàn bộ lập luận qua các vòng debate
    consensus_note: str             # Ghi chú tổng kết đồng thuận


class VerifiedResult(BaseModel):
    """Đầu ra cuối cùng gửi cho agent downstream khi toàn bộ câu đã thỏa mãn."""
    exam_id: str
    student_id: Optional[str] = None
    session_id: Optional[str] = None
    questions: list[VerifiedQuestion]
    total_questions: int
    total_correct: int
    total_score: float


# ── Verifier internal models ───────────────────────────────────────────────────

class VerifierVerdict(BaseModel):
    """Quyết định của Verifier cho 1 câu hỏi."""
    question_id: str
    agreed: bool                    # True → đồng ý với Teacher
    confidence: float               # 0.0 → 1.0
    feedback: list[str]             # Nếu disagreed, feedback gửi lại Teacher
    reasoning: str                  # Lập luận của Verifier
    suggested_score: Optional[float] = None


class VerifierBatchVerdict(BaseModel):
    """Kết quả verify toàn bộ batch."""
    verdicts: list[VerifierVerdict]


# ── VerifierState ──────────────────────────────────────────────────────────────

class VerifierState(TypedDict):
    debate_state: DebateState               # Nhận từ Teacher
    verdicts: list[VerifierVerdict]         # Verdict hiện tại của từng câu
    pending_question_ids: list[str]         # Câu chưa thỏa mãn
    satisfied_question_ids: list[str]       # Câu đã thỏa mãn
    phase: Literal["verify", "finalize"]


# ── VerifierAgent ──────────────────────────────────────────────────────────────

class VerifierAgent(BaseAgent, ToolRegistry):
    def __init__(self):
        super().__init__(agent_role="verifier")
        self.memory             = MemorySaver()
        self.graph              = None

    # ── Setup ──────────────────────────────────────────────────────────────────

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

        # Sau verify: nếu còn pending → trả về Teacher (END),
        # nếu tất cả thỏa mãn → finalize
        builder.add_conditional_edges(
            "verify",
            self._route_after_verify,
            {"return_to_teacher": END, "finalize": "finalize"},
        )
        builder.add_edge("finalize", END)

        return builder.compile(checkpointer=self.memory)

    # ── Routing ────────────────────────────────────────────────────────────────

    def _route_after_verify(self, state: VerifierState) -> str:
        if state["pending_question_ids"]:
            return "return_to_teacher"
        return "finalize"

    # ── Verify Phase (batch, song song) ───────────────────────────────────────

    async def _verify_single(
        self,
        output: Output,
        exam_id: Optional[str],
    ) -> VerifierVerdict:
        sa       = output.student_ans
        question = await tools.get_data(
            "masterthpt", "questions", query={"id": sa.question_id}
        )
        teacher_result = (
            output.debate_result.model_dump() if output.debate_result
            else output.draft_result.model_dump() if output.draft_result
            else "Chưa có kết quả"
        )
        prompt = f"""Bạn là Verifier — kiểm tra độc lập kết quả chấm thi.
Bạn PHẢI dùng tools để tìm bằng chứng trước khi ra quyết định.

Câu hỏi           : {question}
Trả lời HS        : {sa.answer}
Đáp án            : {sa.correct_answer}
Kết quả Teacher   : {teacher_result}
Feedback trước đó : {output.verifier_feedback}

Tra cứu bằng chứng, sau đó quyết định agreed=True/False với lập luận rõ ràng.
question_id phải là: {sa.question_id}"""

        result: VerifierVerdict = await self._run_with_tools(prompt, VerifierVerdict)
        result.question_id = sa.question_id
        return result
    
    async def _verify_batch(self, state: VerifierState) -> VerifierState:
        debate_state = state["debate_state"]
        exam_id      = debate_state.get("exam_id")

        # Chỉ verify những câu còn pending
        pending_ids = set(state["pending_question_ids"])
        targets     = [
            o for o in debate_state["outputs"]
            if o.student_ans.question_id in pending_ids
        ]

        new_verdicts: list[VerifierVerdict] = await asyncio.gather(
            *[self._verify_single(o, exam_id) for o in targets]
        )

        # Merge verdict cũ + mới (ghi đè theo question_id)
        verdict_map = {v.question_id: v for v in state["verdicts"]}
        for v in new_verdicts:
            verdict_map[v.question_id] = v

        # Cập nhật verifier_feedback vào outputs của DebateState
        output_map = {
            o.student_ans.question_id: o
            for o in debate_state["outputs"]
        }
        for v in new_verdicts:
            if not v.agreed and v.question_id in output_map:
                output_map[v.question_id] = output_map[v.question_id].model_copy(
                    update={"verifier_feedback": v.feedback}
                )

        updated_outputs = list(output_map.values())

        # Phân loại pending / satisfied
        all_verdicts      = list(verdict_map.values())
        still_pending     = [
            v.question_id for v in all_verdicts
            if not v.agreed
        ]
        now_satisfied     = [
            v.question_id for v in all_verdicts
            if v.agreed
        ]

        # Cập nhật debate_state với outputs mới
        updated_debate_state = {
            **debate_state,
            "outputs": updated_outputs,
            "phase": "debate",          # Báo Teacher chạy debate phase tiếp
        }

        return {
            **state,
            "debate_state":           updated_debate_state,
            "verdicts":               all_verdicts,
            "pending_question_ids":   still_pending,
            "satisfied_question_ids": now_satisfied,
            "phase": "verify",
        }

    # ── Finalize Phase ─────────────────────────────────────────────────────────

    async def _finalize(self, state: VerifierState) -> VerifierState:
        """Tổng hợp tất cả câu đã thỏa mãn → VerifiedResult."""
        debate_state = state["debate_state"]
        verdict_map  = {v.question_id: v for v in state["verdicts"]}
        output_map   = {
            o.student_ans.question_id: o
            for o in debate_state["outputs"]
        }

        questions: list[VerifiedQuestion] = []
        for qid, output in output_map.items():
            verdict      = verdict_map.get(qid)
            draft        = output.draft_result
            debate       = output.debate_result

            # Gom reasoning chain
            reasoning_chain = []
            if draft:
                reasoning_chain.append(f"[Draft] {draft.reasoning}")
            if debate:
                reasoning_chain.append(f"[Debate] {debate.teacher_rebuttal}")
            if verdict:
                reasoning_chain.append(f"[Verifier] {verdict.reasoning}")

            final_score = (
                debate.final_score if debate and debate.final_score is not None
                else draft.score if draft
                else verdict.suggested_score if verdict
                else None
            )
            is_correct = (
                debate.accepted_verifier
                if debate
                else draft.is_correct if draft
                else False
            )

            questions.append(VerifiedQuestion(
                exam_id        = debate_state.get("exam_id", ""),
                question_id    = qid,
                final_score    = final_score,
                is_correct     = is_correct,
                reasoning_chain= reasoning_chain,
                consensus_note = verdict.reasoning if verdict else "",
            ))

        total_correct = sum(1 for q in questions if q.is_correct)
        total_score   = sum(q.final_score or 0.0 for q in questions)

        verified = VerifiedResult(
            exam_id         = debate_state.get("exam_id", ""),
            student_id      = debate_state.get("student_id"),
            session_id      = debate_state.get("session_id"),
            questions       = questions,
            total_questions = len(questions),
            total_correct   = total_correct,
            total_score     = total_score,
        )

        return {**state, "_verified_result": verified}

    # ── Public API ─────────────────────────────────────────────────────────────

    async def verify(
        self,
        debate_state: DebateState,
        thread_id: str = "default",
    ) -> tuple[Literal["disagree", "agree"], DebateState | VerifiedResult]:
        """
        Nhận DebateState từ Teacher.

        Returns:
            ("disagree", DebateState)    → Verifier phản đối, trả DebateState
                                           có verifier_feedback để Teacher debate tiếp
            ("agree",    VerifiedResult) → Tất cả thỏa mãn, trả kết quả cuối
        """
        all_question_ids = [
            o.student_ans.question_id
            for o in debate_state["outputs"]
        ]

        init_state: VerifierState = {
            "debate_state":           debate_state,
            "verdicts":               [],
            "pending_question_ids":   all_question_ids,
            "satisfied_question_ids": [],
            "phase":                  "verify",
        }

        config       = {"configurable": {"thread_id": thread_id}}
        final_state  = await self.graph.ainvoke(init_state, config=config)

        # Còn pending → disagree, trả DebateState để Teacher debate tiếp
        if final_state["pending_question_ids"]:
            return "disagree", final_state["debate_state"]

        # Tất cả thỏa mãn → agree, trả VerifiedResult
        return "agree", final_state["_verified_result"]

    async def run(self, input: str) -> str:
        return "Use verify(debate_state) instead."