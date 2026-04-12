from typing import List, Optional, Literal, Any
from typing_extensions import TypedDict
from enum import Enum
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from master.agents import BaseAgent
from master.agents.common.message import StudentAnswer, ExamSection, Intent, MessageRequest
from master.agents.common import tools
from master.agents.common.tools import ToolRegistry
from master.agents.common.llm_client import LLMClient

import asyncio

load_dotenv(override=True)

# ── Metadata schemas (parse từ MessageRequest.metadata) ───────────────────────

class GradeSubmissionMeta(BaseModel):
    """GRADE_SUBMISSION — teacher nhận file, tự extract câu trả lời rồi chấm."""
    file_urls: list[str]


class ViewAnalysisMeta(BaseModel):
    """VIEW_ANALYSIS — đã có student_answers, teacher chấm + debate."""
    exam_id: str
    student_id: str
    session_id: str
    total_questions: int
    exam_sections: list[ExamSection]
    student_answers: list[StudentAnswer]


# ── Grading models ─────────────────────────────────────────────────────────────

class DraftResult(BaseModel):
    question_id: str
    is_correct: bool
    score: Optional[float] = None
    reasoning: str      # Lập luận chấm điểm
    feedback: str       # Nhận xét gửi cho Verifier


class DebateResult(BaseModel):
    question_id: str
    teacher_rebuttal: str       # Phản biện hoặc đồng ý với Verifier
    final_feedback: str         # Nhận xét tổng hợp cuối cùng
    final_score: Optional[float] = None
    accepted_verifier: bool     # Có chấp nhận ý kiến Verifier không


class Output(BaseModel):
    """Unit xử lý cho một câu hỏi — xuyên suốt toàn pipeline."""
    student_ans: StudentAnswer              # KHÔNG thay đổi
    draft_result: Optional[DraftResult] = None
    verifier_feedback: list[str] = Field(default_factory=list)
    debate_result: Optional[DebateResult] = None


# ── DebateState ────────────────────────────────────────────────────────────────

class DebateState(TypedDict):
    # Core grading state
    outputs: list[Output]
    round: int
    max_round: int
    phase: Literal["draft", "debate"]

    # Context giữ nguyên từ MessageRequest để truyền downstream
    intent: Intent
    exam_id: Optional[str]
    student_id: Optional[str]
    session_id: Optional[str]
    raw_request: MessageRequest             # Toàn bộ request gốc


# ── TeacherAgent (subgraph) ────────────────────────────────────────────────────

class TeacherAgent(BaseAgent, ToolRegistry):
    def __init__(self):
        super().__init__(agent_role="teacher")
        self._llm_extractor = None          # Extract StudentAnswer từ file
        self.browser        = None
        self.playwright     = None
        self.memory         = MemorySaver()
        self.graph          = None

    # ── Setup ──────────────────────────────────────────────────────────────────

    async def setup(self):
        await self.setup_tools(LLMClient.chat_model())
        self.graph = self._build_graph()

    def _build_graph(self):
        builder = StateGraph(DebateState)

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

    # ── Intent → DebateState ───────────────────────────────────────────────────

    async def _build_state_from_request(
        self,
        request: MessageRequest,
        max_round: int = 3,
    ) -> DebateState:
        """
        Parse MessageRequest theo intent, trả về DebateState sẵn sàng chạy.
        Teacher chỉ xử lý GRADE_SUBMISSION và VIEW_ANALYSIS.
        """
        match request.intent:

            case Intent.GRADE_SUBMISSION:
                meta = GradeSubmissionMeta(
                    file_urls=request.file_urls or request.metadata.get("file_urls", [])
                )
                # Extract StudentAnswer từ từng file (song song)
                outputs = await asyncio.gather(
                    *[self._extract_answer_from_file(url) for url in meta.file_urls]
                )
                return DebateState(
                    outputs=list(outputs),
                    round=0,
                    max_round=max_round,
                    phase="draft",
                    intent=request.intent,
                    exam_id=None,
                    student_id=None,
                    session_id=None,
                    raw_request=request,
                )

            case Intent.VIEW_ANALYSIS:
                meta = ViewAnalysisMeta(**request.metadata)
                outputs = [
                    Output(student_ans=sa)
                    for sa in meta.student_answers
                ]
                return DebateState(
                    outputs=outputs,
                    round=0,
                    max_round=max_round,
                    phase="draft",
                    intent=request.intent,
                    exam_id=meta.exam_id,
                    student_id=meta.student_id,
                    session_id=meta.session_id,
                    raw_request=request,
                )

            case _:
                raise ValueError(
                    f"TeacherAgent không xử lý intent: {request.intent}. "
                    f"Chỉ hỗ trợ GRADE_SUBMISSION và VIEW_ANALYSIS."
                )

    # ── File extraction ────────────────────────────────────────────────────────

    async def _extract_answer_from_file(self, file_url: str) -> Output:
        """Dùng LLM extract StudentAnswer từ file (ảnh bài làm, PDF,...)."""
        prompt = f"""Từ file sau, hãy trích xuất thông tin bài làm của học sinh.
File URL: {file_url}
Trả về đúng định dạng StudentAnswer với các trường: exam_id, question_id, answer, correct_answer, file_urls."""

        student_ans: StudentAnswer = await asyncio.to_thread(
            self._llm_extractor.invoke, prompt
        )
        student_ans.file_urls = [file_url]
        return Output(student_ans=student_ans)

    # ── Draft Phase ────────────────────────────────────────────────────────────

    async def _draft_single(self, output: Output) -> Output:
        sa       = output.student_ans
        question = await tools.get_data(
            "masterthpt", "questions", query={"id": sa.question_id}
        )
        prompt = f"""Bạn là giáo viên chấm thi chuyên nghiệp.
Bạn có thể dùng tools để tra cứu thêm tài liệu, tìm kiếm thông tin liên quan trước khi chấm.

Câu hỏi      : {question}
Trả lời HS   : {sa.answer}
Đáp án       : {sa.correct_answer}
File đính kèm: {sa.file_urls or "Không có"}

Hãy tra cứu nếu cần, sau đó chấm điểm và đưa ra nhận xét để Verifier kiểm tra.
question_id phải là: {sa.question_id}"""

        result: DraftResult = await self._run_with_tools(prompt, DraftResult)
        result.question_id = sa.question_id
        return output.model_copy(update={"draft_result": result})


    async def _draft_batch(self, state: DebateState) -> DebateState:
        updated = await asyncio.gather(
            *[self._draft_single(o) for o in state["outputs"]]
        )
        return {**state, "outputs": list(updated)}

    # ── Debate Phase ───────────────────────────────────────────────────────────

    async def _debate_single(self, output: Output) -> Output:
        sa       = output.student_ans
        question = await tools.get_data(
            "masterthpt", "questions", query={"id": sa.question_id}
        )
        prompt = f"""Bạn là giáo viên đang tranh luận với Verifier.
Bạn PHẢI dùng tools để tìm bằng chứng củng cố hoặc bác bỏ feedback của Verifier.

Câu hỏi           : {question}
Trả lời HS        : {sa.answer}
Đáp án            : {sa.correct_answer}
Chấm nháp của bạn : {output.draft_result.model_dump() if output.draft_result else "Chưa có"}
Feedback Verifier : {output.verifier_feedback}

Tra cứu bằng chứng, sau đó phản biện hoặc đồng ý có lập luận.
question_id phải là: {sa.question_id}"""

        result: DebateResult = await self._run_with_tools(prompt, DebateResult)
        result.question_id = sa.question_id
        return output.model_copy(update={"debate_result": result})

    async def _debate_batch(self, state: DebateState) -> DebateState:
        updated = await asyncio.gather(
            *[self._debate_single(o) for o in state["outputs"]]
        )
        return {
            **state,
            "outputs": list(updated),
            "round": state["round"] + 1,
        }

    # ── Public API ─────────────────────────────────────────────────────────────

    async def run_draft(
        self,
        request: MessageRequest,
        max_round: int = 3,
        thread_id: str = "default",
    ) -> DebateState:
        """Nhận MessageRequest → build state → chạy draft phase."""
        state  = await self._build_state_from_request(request, max_round)
        config = {"configurable": {"thread_id": thread_id}}
        return await self.graph.ainvoke(state, config=config)

    async def run_debate(
        self,
        state: DebateState,
        thread_id: str = "default",
    ) -> DebateState:
        """Nhận DebateState đã có verifier_feedback → chạy debate phase."""
        config = {"configurable": {"thread_id": thread_id}}
        return await self.graph.ainvoke({**state, "phase": "debate"}, config=config)

    async def run(self, input: str) -> str:
        return "Use run_draft(MessageRequest) or run_debate(DebateState)."


# ── Demo ───────────────────────────────────────────────────────────────────────

async def main():
    teacher = TeacherAgent()
    await teacher.setup()

    # ── Simulate: VIEW_ANALYSIS từ NestJS ─────────────────────────────────────
    request = MessageRequest(
        intent=Intent.VIEW_ANALYSIS,
        user_message="Chấm bài thi cho học sinh",
        student_id="student-001",
        metadata={
            "exam_id":         "bed1f84d-329c-5ab3-876e-84dbaaa96c13",
            "student_id":      "student-001",
            "session_id":      "session-abc",
            "total_questions": 2,
            "exam_sections":   [],
            "student_answers": [
                {
                    "exam_id":        "bed1f84d-329c-5ab3-876e-84dbaaa96c13",
                    "question_id":    "07931d51-d61b-5a58-bb3b-351a8edccbcd",
                    "answer":         "B",
                    "correct_answer": "A",
                    "file_urls":      [],
                },
                {
                    "exam_id":        "bed1f84d-329c-5ab3-876e-84dbaaa96c13",
                    "question_id":    "c7b9433a-e22e-5f91-9a8e-6e682612f748",
                    "answer":         "C",
                    "correct_answer": "A",
                    "file_urls":      [],
                },
            ],
        },
    )

    # Phase 1: Draft
    draft_state = await teacher.run_draft(request, thread_id="exam-001")
    print("=== DRAFT ===")
    for o in draft_state["outputs"]:
        print(o.draft_result)

    # Simulate Verifier thêm feedback vào outputs
    draft_state["outputs"][0] = draft_state["outputs"][0].model_copy(
        update={"verifier_feedback": ["Đáp án B cũng có thể chấp nhận trong ngữ cảnh này"]}
    )
    draft_state["outputs"][1] = draft_state["outputs"][1].model_copy(
        update={"verifier_feedback": ["Học sinh trả lời C là hoàn toàn sai"]}
    )

    # Phase 2: Debate
    final_state = await teacher.run_debate(draft_state, thread_id="exam-001")
    print("\n=== DEBATE ===")
    for o in final_state["outputs"]:
        print(o.debate_result)


if __name__ == "__main__":
    asyncio.run(main())