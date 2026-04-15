from typing import List, Optional, Literal
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from dotenv import load_dotenv
from pydantic import BaseModel
from master.agents import BaseAgent
from master.agents.common.tools import ToolsRegistry
from master.agents.common.llm_client import LLMClient
from master.agents.common.message import MessageResponse
from master.agents.common.state import AgentState
from master.agents.teacher import Output
import os

import asyncio

load_dotenv(override=True)


# ── Verifier internal models ───────────────────────────────────────────────────

class VerifierVerdict(BaseModel):
    question_id: str
    agreed: bool
    confidence: float
    feedback: list[str]
    reasoning: str
    suggested_score: Optional[float] = None


class VerifierBatchVerdict(BaseModel):
    verdicts: list[VerifierVerdict]


class FinalSummary(BaseModel):
    feedback: str


class VerifierAgent(ToolsRegistry, BaseAgent):
    def __init__(self):
        super().__init__(agent_role="Verifier")
        self._llm = None
        self._llm_verdict = None
        self._llm_summary = None
        self.memory = MemorySaver()
        self.graph = None

    async def setup(self):
        self.logger.agent_node("Verifier setup started")
        llm = LLMClient.chat_model(
            provider="openai_compatible",
            base_url=os.getenv("FPT_BASE_URL"),
            api_key=os.getenv("FPT_API_KEY"),
            model="Qwen3-32B",
        )
        await self.setup_tools(llm)
        self._llm_verdict = self._llm.with_structured_output(
            VerifierBatchVerdict
        )
        self._llm_summary = self._llm.with_structured_output(FinalSummary)
        self.graph = self._build_graph()
        self.logger.agent_node("Verifier setup completed")

    def _build_graph(self):
        builder = StateGraph(AgentState)

        builder.add_node("verify",   self._verify_batch)
        builder.add_node("finalize", self._finalize)
        builder.add_node("tools",    self.get_tool_node())

        builder.add_conditional_edges(
            START,
            lambda s: s["phase"],
            {"verify": "verify", "finalize": "finalize"},
        )

        builder.add_conditional_edges(
            "verify",
            self._route_after_verify,
            {"return_to_teacher": END, "finalize": "finalize"},
        )
        builder.add_conditional_edges(
            "finalize",
            self._route_after_finalize,
            {"tools": "tools", "done": END},
        )
        builder.add_edge("tools", END)

        return builder.compile(checkpointer=self.memory)

    def _route_after_verify(self, state: AgentState) -> str:
        verdicts: list[VerifierVerdict] = state.get("_verdicts", [])
        pending = [v for v in verdicts if not v.agreed]
        if pending:
            return "return_to_teacher"
        return "finalize"

    def _route_after_finalize(self, state: AgentState) -> str:
        if state.get("enable_verifier_tools_node", False):
            return "tools"
        return "done"

    async def _verify_single(
        self,
        output: Output,
        exam_id: Optional[str],
    ) -> VerifierVerdict:
        sa = output.student_ans
        self.logger.agent_node(f"Verifier verify start question_id={sa.question_id}")
        question = await self.get_data(
            "masterthpt", "questions", query={"id": sa.question_id}
        )

        teacher_grade = "Chưa chấm"
        if output.draft_result:
            teacher_grade = f"{'Đúng' if output.draft_result.is_correct else 'Sai'} (Điểm: {output.draft_result.score})"
        
        prompt = f"""Kiểm tra viên: Kiểm tra xem trả lời là Đúng hay Sai. Nhận xét của giáo viên: {teacher_grade}
            Câu hỏi: {question}
            Trả lời học sinh: {sa.student_answer}
            Trả về JSON với các trường: agreed, confidence (0-1), feedback (list), reasoning
            question_id: {sa.question_id}"""

        verdict_batch: VerifierBatchVerdict = await self._run_with_tools(
            prompt,
            output_schema=VerifierBatchVerdict,
            max_tool_rounds=3
        )
        result = (
            verdict_batch.verdicts[0]
            if verdict_batch.verdicts
            else VerifierVerdict(
                question_id=sa.question_id,
                agreed=True,
                confidence=0.5,
                feedback=[],
                reasoning="No model response",
            )
        )
        result.question_id = sa.question_id
        self.logger.agent_node(
            f"Verifier verify end question_id={sa.question_id} agreed={result.agreed}"
        )
        return result

    async def _verify_batch(self, state: AgentState) -> AgentState:
        outputs: list[Output] = state.get("debate_outputs", [])

        old_verdicts: list[VerifierVerdict] = state.get("_verdicts", [])
        satisfied_ids: set[str] = {v.question_id for v in old_verdicts if v.agreed}

        targets = [o for o in outputs if o.student_ans.question_id not in satisfied_ids]

        tasks = [asyncio.create_task(self._verify_single(o, state.get("exam_id"))) for o in targets]
        new_verdicts: list[VerifierVerdict] = []

        for task in asyncio.as_completed(tasks):
            verdict = await task
            new_verdicts.append(verdict)

        verdict_map = {v.question_id: v for v in old_verdicts}
        for v in new_verdicts:
            verdict_map[v.question_id] = v

        all_verdicts = list(verdict_map.values())
        output_map = {o.student_ans.question_id: o for o in outputs}
        for v in new_verdicts:
            if not v.agreed and v.question_id in output_map:
                output_map[v.question_id] = output_map[v.question_id].model_copy(
                    update={"verifier_feedback": v.feedback}
                )

        return {
            **state,
            "debate_outputs": list(output_map.values()),
            "_verdicts":      all_verdicts,
            "phase":          "verify",
        }

    # ── Finalize Phase ─────────────────────────────────────────────────────────

    async def _finalize(self, state: AgentState) -> AgentState:
        outputs: list[Output]          = state.get("debate_outputs", [])
        verdicts: list[VerifierVerdict] = state.get("_verdicts", [])
        verdict_map = {v.question_id: v for v in verdicts}
        request     = state.get("request")

        lines = []
        for output in outputs:
            qid     = output.student_ans.question_id
            verdict = verdict_map.get(qid)
            draft   = output.draft_result
            debate  = output.debate_result

            parts = []
            if draft:
                parts.append(f"[Draft] {draft.reasoning}")
            if debate:
                parts.append(f"[Debate] {debate.teacher_rebuttal}")
            if verdict:
                parts.append(f"[Verifier] {verdict.reasoning}")

            is_correct = (
                debate.accepted_verifier if debate
                else draft.is_correct if draft
                else False
            )
            score = (
                debate.final_score if debate and debate.final_score is not None
                else draft.score if draft
                else verdict.suggested_score if verdict
                else None
            )
            lines.append(
                f"Câu {qid}: {'Đúng' if is_correct else 'Sai'}"
                + (f" ({score} điểm)" if score is not None else "")
                + " | " + " | ".join(parts)
            )

        summary_prompt = (
            "Dựa trên kết quả chấm và phân tích dưới đây, hãy viết một đoạn nhận xét ngắn gọn cho học sinh:\n\n"
            + "\n".join(lines)
        )

        summary: FinalSummary = await asyncio.to_thread(
            self._llm_summary.invoke, summary_prompt
        )

        response = MessageResponse(
            student_id  = request.student_id if request else "",
            exam_id     = state.get("exam_id") or (request.exam_id if request else None),
            question_id = request.question_id if request else None,
            feedback    = summary.feedback,
        )

        return {**state, "response": response, "phase": "finalize"}

    # ── Public API ─────────────────────────────────────────────────────────────

    async def verify(
        self,
        state: AgentState,
        thread_id: str = "default",
    ) -> tuple[Literal["disagree", "agree"], AgentState]:
        """Verify grading and return disagreement status.

        Returns:
            ("disagree", AgentState) → Verifier disagreed, AgentState contains verifier_feedback
            ("agree", AgentState) → All questions passed, state contains final response
        """
        self.logger.agent_node(f"Verifier verify called thread_id={thread_id}")
        state  = {**state, "phase": "verify"}
        config = {"configurable": {"thread_id": thread_id}}
        final  = await self.graph.ainvoke(state, config=config)

        verdicts: list[VerifierVerdict] = final.get("_verdicts", [])
        still_pending = [v for v in verdicts if not v.agreed]

        if still_pending:
            self.logger.agent_node("Verifier verify result=disagree")
            return "disagree", final

        self.logger.agent_node("Verifier verify result=agree")
        return "agree", final

    async def run(self, input: str) -> str:
        return "Use verify(state) instead."