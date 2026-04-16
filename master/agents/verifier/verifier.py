from typing import List, Optional, Literal
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from dotenv import load_dotenv
from pydantic import BaseModel
from master.agents import BaseAgent
from master.agents.common.tools import ToolsRegistry
from master.agents.common.llm_client import LLMClient
from master.agents.common.message import MessageResponse, Intent
from master.agents.common.state import AgentState
from master.agents.common.prompt import (
    verifier_batch_prompt,
    verifier_mode_instruction,
    verifier_summary_prompt,
)
from master.agents.teacher import Output
import os
import json

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
        # Trong pipeline chuẩn, Teacher đã setup shared tools trước.
        # Verifier chỉ attach lại để tránh setup_tools lặp.
        if ToolsRegistry._shared_tools is None:
            await self.setup_tools(llm)
        else:
            self._attach_shared_tools_to_agent(llm)
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

    async def _verify_batch(self, state: AgentState) -> AgentState:
        outputs: list[Output] = state.get("debate_outputs", [])

        old_verdicts: list[VerifierVerdict] = state.get("_verdicts", [])
        satisfied_ids: set[str] = {v.question_id for v in old_verdicts if v.agreed}

        targets = [o for o in outputs if o.student_ans.question_id not in satisfied_ids]

        new_verdicts: list[VerifierVerdict] = []
        if targets:
            try:
                try:
                    llm_batch_size = max(1, int(os.getenv("VERIFIER_LLM_BATCH_SIZE", "6")))
                except ValueError:
                    llm_batch_size = 6
                try:
                    max_question_chars = max(1, int(os.getenv("VERIFIER_MAX_QUESTION_CHARS", "800")))
                except ValueError:
                    max_question_chars = 800

                def _is_length_limit_error(exc: Exception) -> bool:
                    msg = str(exc).lower()
                    return (
                        "length limit" in msg
                        or "maximum context length" in msg
                        or "too many tokens" in msg
                        or "max_tokens" in msg
                    )

                question_ids = [o.student_ans.question_id for o in targets]
                question_docs = await self.get_data(
                    "masterthpt",
                    "questions",
                    query={"id": {"$in": question_ids}},
                    length=max(len(question_ids), 1),
                )
                question_map = {str(q.get("id")): q for q in question_docs}
                for q in (state.get("questions", []) or []):
                    q_dict = q.model_dump() if hasattr(q, "model_dump") else dict(q)
                    qid = str(q_dict.get("id") or "")
                    if qid and qid not in question_map:
                        question_map[qid] = q_dict

                items: list[dict] = []
                solve_mode = True
                for output in targets:
                    sa = output.student_ans
                    teacher_grade = "Chưa chấm"
                    if output.draft_result:
                        teacher_grade = (
                            f"{'Đúng' if output.draft_result.is_correct else 'Sai'} "
                            f"(Điểm: {output.draft_result.score})"
                        )

                    q_doc = question_map.get(sa.question_id, {})
                    q_payload = {
                        "id": q_doc.get("id"),
                        "question_index": q_doc.get("question_index"),
                        "type": q_doc.get("type"),
                        "content": q_doc.get("content"),
                        "content_latex": q_doc.get("content_latex"),
                        "options": q_doc.get("options"),
                        "correct_answer": q_doc.get("correct_answer"),
                    }
                    q_payload = {k: v for k, v in q_payload.items() if v not in (None, "", [])}
                    q_text = json.dumps(q_payload or q_doc, ensure_ascii=False, default=str)
                    if len(q_text) > max_question_chars:
                        q_text = q_text[:max_question_chars] + " ...[truncated]"

                    student_answer = (sa.student_answer or "").strip()
                    if student_answer:
                        solve_mode = False

                    items.append(
                        {
                            "question_id": sa.question_id,
                            "teacher_grade": teacher_grade,
                            "student_answer": student_answer,
                            "question": q_text,
                        }
                    )

                mode_instruction = verifier_mode_instruction(solve_mode)

                self.logger.agent_node(
                    f"Verifier batching items={len(items)} llm_batch_size={llm_batch_size} max_q_chars={max_question_chars}"
                )

                verdict_by_qid: dict[str, VerifierVerdict] = {}

                async def _run_chunk(chunk_items: list[dict]) -> None:
                    prompt = verifier_batch_prompt(
                        mode_instruction=mode_instruction,
                        batch_input_json=json.dumps(chunk_items, ensure_ascii=False, default=str),
                    )
                    try:
                        verdict_batch: VerifierBatchVerdict = await asyncio.to_thread(
                            self._llm_verdict.invoke,
                            prompt,
                        )
                        by_qid = {v.question_id: v for v in (verdict_batch.verdicts or [])}

                        for item in chunk_items:
                            qid = item["question_id"]
                            verdict = by_qid.get(qid)
                            if verdict is None:
                                verdict = VerifierVerdict(
                                    question_id=qid,
                                    agreed=True,
                                    confidence=0.3,
                                    feedback=["Verifier fallback: missing result in batch output."],
                                    reasoning="Missing verdict for this question in the batch output.",
                                )
                            verdict.question_id = qid
                            verdict.confidence = max(0.0, min(1.0, float(verdict.confidence)))
                            verdict_by_qid[qid] = verdict
                    except Exception as exc:
                        if _is_length_limit_error(exc) and len(chunk_items) > 1:
                            mid = len(chunk_items) // 2
                            self.logger.warning(
                                "Verifier chunk exceeded model length; splitting chunk "
                                f"size={len(chunk_items)} into {mid} and {len(chunk_items) - mid}"
                            )
                            await _run_chunk(chunk_items[:mid])
                            await _run_chunk(chunk_items[mid:])
                            return

                        self.logger.warning(
                            "Verifier chunk failed; using deterministic fallback for "
                            f"{len(chunk_items)} item(s): {exc}"
                        )
                        for item in chunk_items:
                            qid = item["question_id"]
                            verdict_by_qid[qid] = VerifierVerdict(
                                question_id=qid,
                                agreed=True,
                                confidence=0.2,
                                feedback=["Verifier fallback used because the batch failed."],
                                reasoning="Verifier batch failed; generated fallback verdict.",
                            )

                for i in range(0, len(items), llm_batch_size):
                    await _run_chunk(items[i:i + llm_batch_size])

                new_verdicts = [verdict_by_qid[qid] for qid in question_ids]

            except Exception as e:
                self.logger.warning(f"Verifier batch mode failed, using deterministic fallback: {e}")
                for o in targets:
                    qid = o.student_ans.question_id
                    new_verdicts.append(
                        VerifierVerdict(
                            question_id=qid,
                            agreed=True,
                            confidence=0.2,
                            feedback=["Verifier fallback used because the batch failed."],
                            reasoning="Verifier batch failed; generated fallback verdict.",
                        )
                    )

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
        is_preprocess = bool(request and request.intent == Intent.PREPROCESS)

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

        if is_preprocess:
            solved_lines = []
            for output in outputs:
                qid = output.student_ans.question_id
                verdict = verdict_map.get(qid)
                draft = output.draft_result
                debate = output.debate_result

                confidence = (
                    float(getattr(verdict, "confidence", 0.0))
                    if verdict is not None
                    else float(getattr(draft, "confidence", 0.0))
                    if draft is not None
                    else 0.0
                )
                reasoning = (
                    debate.final_feedback if debate and debate.final_feedback
                    else draft.feedback if draft and draft.feedback
                    else verdict.reasoning if verdict and verdict.reasoning
                    else "Da xu ly cau hoi o che do PREPROCESS."
                )
                solved_lines.append(
                    f"Cau {qid}: confidence={confidence:.2f} | {reasoning}"
                )

            summary_text = (
                "PREPROCESS hoan tat. Da giai va xac minh cac cau hoi:\n"
                + "\n".join(solved_lines)
                if solved_lines
                else "PREPROCESS hoan tat nhung khong co cau hoi de tong hop."
            )
        else:
            summary_prompt = verifier_summary_prompt(lines)

            summary: FinalSummary = await asyncio.to_thread(
                self._llm_summary.invoke, summary_prompt
            )
            summary_text = summary.feedback

        response = MessageResponse(
            student_id  = request.student_id if request else "",
            exam_id     = state.get("exam_id") or (request.exam_id if request else None),
            question_id = request.question_id if request else None,
            feedback    = summary_text,
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