from typing import Any, Awaitable, Callable, List, Optional, Literal
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from master.agents import BaseAgent
from master.agents.common.message import StudentAnswer
from master.agents.common.tools import ToolsRegistry
from master.agents.common.llm_client import LLMClient

import asyncio
import os

load_dotenv(override=True)


# ── Pydantic Models ────────────────────────────────────────────────────────────

class DraftResult(BaseModel):
    """Kết quả chấm nháp của Teacher."""
    question_id: str
    is_correct: bool
    score: Optional[float] = None
    reasoning: str                      # Lập luận chấm điểm
    feedback: str                       # Nhận xét gửi cho Verifier


class DebateResult(BaseModel):
    """Kết quả tranh luận sau khi nhận feedback từ Verifier."""
    question_id: str
    teacher_rebuttal: str               # Phản biện hoặc đồng ý với Verifier
    final_feedback: str                 # Nhận xét tổng hợp cuối
    final_score: Optional[float] = None
    accepted_verifier: bool             # Có chấp nhận ý kiến Verifier không


class Output(BaseModel):
    """Unit xử lý cho một câu hỏi xuyên suốt cả pipeline."""
    student_ans: StudentAnswer          # KHÔNG thay đổi
    draft_result: Optional[DraftResult] = None
    verifier_feedback: List[str] = Field(default_factory=list)
    debate_result: Optional[DebateResult] = None


# ── Teacher Agent ──────────────────────────────────────────────────────────────

class TeacherAgent(ToolsRegistry, BaseAgent):
    def __init__(self):
        super().__init__(agent_role="teacher")
        self._llm        = None
        self._llm_draft  = None         # structured output → DraftResult
        self._llm_debate = None         # structured output → DebateResult
        self.memory      = MemorySaver()
        self.graph       = None
        self._event_callback: Optional[Callable[[dict[str, Any]], Awaitable[None] | None]] = None

    # ── Setup ──────────────────────────────────────────────────────────────────

    async def setup(self):
        self.logger.agent_node("Teacher setup started")
        llm = LLMClient.chat_model(
            provider="openai_compatible",
            base_url=os.getenv("FPT_BASE_URL"),
            api_key=os.getenv("FPT_API_KEY"),
            model="gemma-4-31B-it",
            temperature=0.7,
            max_tokens=2000  # Cân bằng chi phí & timeout
        )
        await self.setup_tools(llm)
        self._llm_draft  = self._llm.with_structured_output(DraftResult)
        self._llm_debate = self._llm.with_structured_output(DebateResult)
        self.graph = self._build_graph()
        self.logger.agent_node("Teacher setup completed")

    def _build_graph(self):
        builder = StateGraph(dict)

        builder.add_node("draft",  self._draft_batch)
        builder.add_node("debate", self._debate_batch)
        builder.add_node("tools",  self.get_tool_node())

        # Routing: phase quyết định node nào chạy
        builder.add_conditional_edges(
            START,
            lambda s: s["phase"],
            {"draft": "draft", "debate": "debate"},
        )
        builder.add_conditional_edges(
            "draft",
            self._route_after_teacher_phase,
            {"tools": "tools", "done": END},
        )
        builder.add_conditional_edges(
            "debate",
            self._route_after_teacher_phase,
            {"tools": "tools", "done": END},
        )
        builder.add_edge("tools", END)

        return builder.compile(checkpointer=self.memory)

    def _route_after_teacher_phase(self, state: dict[str, Any]) -> str:
        if state.get("enable_teacher_tools_node", False):
            return "tools"
        return "done"

    async def _emit_event(self, event: dict[str, Any]):
        if self._event_callback is None:
            return
        result = self._event_callback(event)
        if asyncio.iscoroutine(result):
            await result

    # ── Draft Phase ────────────────────────────────────────────────────────────

    async def _draft_single(self, output: Output) -> Output:
        """Chấm nháp 1 câu hỏi."""
        sa = output.student_ans
        self.logger.agent_node(f"Teacher draft start question_id={sa.question_id}")
        question = await self.get_data(
            "masterthpt", "questions", query={"id": sa.question_id}
        )

        prompt = f"""Giáo viên: Chấm nháp 1 câu hỏi
            Câu hỏi   : {question}
            Trả lời HS: {sa.student_answer}
            Đáp án    : {sa.question_id}

            Hãy chấm điểm, lập luận rõ ràng và đưa ra nhận xét để gửi cho Verifier kiểm tra lại.
            question_id phải là: {sa.question_id}"""

        result: DraftResult = await asyncio.to_thread(
            self._llm_draft.invoke, prompt
        )
        result.question_id = sa.question_id
        self.logger.agent_node(f"Teacher draft end question_id={sa.question_id} score={result.score}")
        return output.model_copy(update={"draft_result": result})

    async def _draft_batch(self, state: dict[str, Any]) -> dict[str, Any]:
        """Chấm nháp toàn bộ debate_outputs song song."""
        outputs: list[Output] = state["debate_outputs"]
        tasks = [asyncio.create_task(self._draft_single(o)) for o in outputs]
        completed: dict[str, Output] = {}

        total = len(tasks)
        done_count = 0
        for task in asyncio.as_completed(tasks):
            out = await task
            done_count += 1
            qid = out.student_ans.question_id
            completed[qid] = out
            await self._emit_event(
                {
                    "type": "agent_partial",
                    "agent": "teacher",
                    "stage": "draft",
                    "question_id": qid,
                    "done": done_count,
                    "total": total,
                    "score": out.draft_result.score if out.draft_result else None,
                    "is_correct": out.draft_result.is_correct if out.draft_result else None,
                }
            )

        ordered = [completed[o.student_ans.question_id] for o in outputs]
        return {**state, "debate_outputs": ordered, "phase": "verify"}

    # ── Debate Phase ───────────────────────────────────────────────────────────

    async def _debate_single(self, output: Output) -> Output:
        """Tranh luận 1 câu hỏi với feedback từ Verifier."""
        sa = output.student_ans
        self.logger.agent_node(f"Teacher debate start question_id={sa.question_id}")
        question = await self.get_data(
            "masterthpt", "questions", query={"id": sa.question_id}
        )

        prompt = f"""Giáo viên: Tranh luận với Verifier về bài chấm
            Câu hỏi          : {question}
            Trả lời HS        : {sa.student_answer}
            Chấm nháp của bạn : {output.draft_result.model_dump() if output.draft_result else "Chưa có"}
            Feedback Verifier : {output.verifier_feedback}

            Hãy phân tích feedback, phản biện hoặc đồng ý có lập luận, và đưa ra nhận xét cuối cùng.
            question_id phải là: {sa.question_id}"""

        result: DebateResult = await asyncio.to_thread(
            self._llm_debate.invoke, prompt
        )
        result.question_id = sa.question_id
        self.logger.agent_node(
            f"Teacher debate end question_id={sa.question_id} final_score={result.final_score}"
        )
        return output.model_copy(update={"debate_result": result})

    async def _debate_batch(self, state: dict[str, Any]) -> dict[str, Any]:
        """Tranh luận toàn bộ debate_outputs song song."""
        outputs: list[Output] = state["debate_outputs"]
        tasks = [asyncio.create_task(self._debate_single(o)) for o in outputs]
        completed: dict[str, Output] = {}

        total = len(tasks)
        done_count = 0
        for task in asyncio.as_completed(tasks):
            out = await task
            done_count += 1
            qid = out.student_ans.question_id
            completed[qid] = out
            await self._emit_event(
                {
                    "type": "agent_partial",
                    "agent": "teacher",
                    "stage": "debate",
                    "question_id": qid,
                    "done": done_count,
                    "total": total,
                    "final_score": out.debate_result.final_score if out.debate_result else None,
                }
            )

        updated = [completed[o.student_ans.question_id] for o in outputs]
        return {
            **state,
            "debate_outputs": list(updated),
            "round": state["round"] + 1,
            "phase": "verify",
        }

    # ── Public API ─────────────────────────────────────────────────────────────

    async def run_draft(
        self,
        state: dict[str, Any],
        thread_id: str = "default",
        on_event: Optional[Callable[[dict[str, Any]], Awaitable[None] | None]] = None,
    ) -> dict[str, Any]:
        """Phase 1: Khởi tạo debate_outputs từ student_answers, chạy draft."""
        self.logger.agent_node(f"Teacher run_draft called thread_id={thread_id}")
        # Khởi tạo debate_outputs nếu chưa có
        if not state.get("debate_outputs"):
            outputs = [
                Output(student_ans=sa)
                for sa in (state.get("student_answers") or [])
            ]
            state = {**state, "debate_outputs": outputs}

        state = {**state, "phase": "draft"}
        config = {"configurable": {"thread_id": thread_id}}
        self._event_callback = on_event
        result = await self.graph.ainvoke(state, config=config)
        self._event_callback = None
        self.logger.agent_node("Teacher run_draft completed")
        return result

    async def run_debate(
        self,
        state: dict[str, Any],
        thread_id: str = "default",
        on_event: Optional[Callable[[dict[str, Any]], Awaitable[None] | None]] = None,
    ) -> dict[str, Any]:
        """Phase 2: Nhận AgentState (đã có verifier_feedback), tranh luận batch."""
        self.logger.agent_node(f"Teacher run_debate called thread_id={thread_id}")
        state = {**state, "phase": "debate"}
        config = {"configurable": {"thread_id": thread_id}}
        self._event_callback = on_event
        result = await self.graph.ainvoke(state, config=config)
        self._event_callback = None
        self.logger.agent_node("Teacher run_debate completed")
        return result

    async def run(self, input: str) -> str:
        return "Use run_draft() or run_debate() instead."