from typing import Any, List, Optional
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from master.agents import BaseAgent
from master.agents.common.message import (
    MessageRequest,
    MessageResponse,
    StudentAnswer,
    PreprocessPayload,
    ExamDocument,
    ExamQuestion,
)
from master.agents.common.tools import ToolsRegistry
from master.agents.common.langsmith import build_langsmith_invoke_config
from master.agents.common.llm_client import LLMClient
from master.agents.common.prompt import (
    teacher_batch_debate_prompt,
    teacher_batch_draft_prompt,
    teacher_draft_mode_instruction,
    teacher_hint_prompt,
    teacher_preprocess_prompt,
)

import asyncio
import json
import re
import uuid
from datetime import datetime, timezone
import os

load_dotenv(override=True)


# ── Pydantic Models ────────────────────────────────────────────────────────────

class DraftResult(BaseModel):
    """Kết quả chấm nháp của Teacher."""
    question_id: str
    is_correct: bool
    score: Optional[float] = None
    confidence: float = 0.5
    reasoning: str                      # Lập luận chấm điểm
    feedback: str                       # Nhận xét gửi cho Verifier


class DraftBatchResult(BaseModel):
    results: list[DraftResult] = Field(default_factory=list)


class DebateResult(BaseModel):
    """Kết quả tranh luận sau khi nhận feedback từ Verifier."""
    question_id: str
    teacher_rebuttal: str               # Phản biện hoặc đồng ý với Verifier
    final_feedback: str                 # Nhận xét tổng hợp cuối
    final_score: Optional[float] = None
    accepted_verifier: bool             # Có chấp nhận ý kiến Verifier không


class DebateBatchResult(BaseModel):
    results: list[DebateResult] = Field(default_factory=list)


class HintResult(BaseModel):
    """Kết quả gợi ý cho intent ASK_HINT."""
    feedback: str


class PreprocessExtractionResult(BaseModel):
    """Structured payload để lưu vào exams/questions collections."""
    exam: ExamDocument
    questions: list[ExamQuestion] = Field(default_factory=list)


class Output(BaseModel):
    """Unit xử lý cho một câu hỏi xuyên suốt cả pipeline."""
    student_ans: StudentAnswer          # KHÔNG thay đổi
    draft_result: Optional[DraftResult] = None
    verifier_feedback: List[str] = Field(default_factory=list)
    debate_result: Optional[DebateResult] = None


# ── Teacher Agent ──────────────────────────────────────────────────────────────

class TeacherAgent(ToolsRegistry, BaseAgent):
    def __init__(self):
        super().__init__(agent_role="Teacher")
        self._llm        = None
        self._llm_draft_batch = None    # structured output → DraftBatchResult
        self._llm_debate_batch = None   # structured output → DebateBatchResult
        self._llm_hint   = None         # structured output → HintResult
        self._llm_preprocess = None     # structured output → PreprocessExtractionResult
        self.memory      = MemorySaver()
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
            agent_role="teacher",
            # max_tokens=2000  # Cân bằng chi phí & timeout
        )
        await self.setup_tools(llm)
        self._llm_draft_batch = self._llm.with_structured_output(DraftBatchResult)
        self._llm_debate_batch = self._llm.with_structured_output(DebateBatchResult)
        self._llm_hint   = self._llm.with_structured_output(HintResult)
        self._llm_preprocess = self._llm.with_structured_output(PreprocessExtractionResult)
        self.graph = self._build_graph()
        self.logger.agent_node("Teacher setup completed")

    @staticmethod
    def _fallback_preprocess_payload(
        parser_output: str,
        request: MessageRequest,
        exam_id: Optional[str],
        image_bucket_url: str,
    ) -> PreprocessPayload:
        lines = [ln.strip() for ln in parser_output.splitlines() if ln.strip()]

        # Fallback parser: tách block theo marker "Câu <n>" để giữ tối đa nội dung OCR.
        blocks: list[str] = []
        current_block: list[str] = []
        seen_question_marker = False

        marker_pattern = re.compile(r"^(?:Cau|Câu)\s*\d+(?:\s*[:.\-)])?", flags=re.IGNORECASE)
        for ln in lines:
            is_marker = bool(marker_pattern.match(ln))
            if is_marker:
                seen_question_marker = True
                if current_block:
                    blocks.append("\n".join(current_block).strip())
                current_block = [ln]
                continue

            if seen_question_marker:
                current_block.append(ln)

        if current_block:
            blocks.append("\n".join(current_block).strip())

        if not blocks:
            text = (parser_output or "").strip()
            blocks = [text[:1800] if text else "Câu 1 (fallback từ OCR)"]

        questions: list[ExamQuestion] = []
        for idx, block in enumerate(blocks, start=1):
            qid = str(uuid.uuid4())
            content = (block or "").strip()
            if not content:
                content = f"Câu {idx} (fallback từ OCR)"
            if len(content) > 2200:
                content = content[:2200] + " ...[truncated]"

            questions.append(
                ExamQuestion(
                    id=qid,
                    question_index=idx,
                    type="multiple_choice",
                    content=content,
                    content_latex=content,
                    options=[],
                    correct_answer=None,
                    has_image=False,
                    image_url=None,
                    difficulty_a=1.0,
                    difficulty_b=0.0,
                    topic_tags=[],
                    max_score=None,
                )
            )

        now_iso = datetime.now(timezone.utc).isoformat()
        resolved_exam_id = exam_id or request.exam_id or str(uuid.uuid4())
        exam_doc = ExamDocument(
            id=resolved_exam_id,
            subject="Toán",
            exam_type="PREPROCESS_OCR",
            grade=12,
            year=datetime.now().year,
            source="OCR_PARSER",
            generated=False,
            total_questions=len(questions),
            duration=90,
            metadata={"parser_fallback": True, "image_bucket_url": image_bucket_url},
            created_at=now_iso,
            questions=[q.id for q in questions],
        )
        return PreprocessPayload(exam=exam_doc, questions=questions)

    @staticmethod
    def _normalize_preprocess_payload(
        payload: PreprocessExtractionResult,
        request: MessageRequest,
        exam_id: Optional[str],
        image_bucket_url: str,
    ) -> PreprocessPayload:
        now_iso = datetime.now(timezone.utc).isoformat()
        resolved_exam_id = exam_id or request.exam_id or payload.exam.id or str(uuid.uuid4())

        normalized_questions: list[ExamQuestion] = []
        for idx, q in enumerate(payload.questions, start=1):
            qid = q.id or str(uuid.uuid4())
            has_image = bool(q.has_image)
            image_url = q.image_url if has_image and q.image_url else (image_bucket_url if has_image else None)

            normalized_questions.append(
                ExamQuestion(
                    id=qid,
                    question_index=int(q.question_index or idx),
                    type=q.type or "multiple_choice",
                    content=(q.content or "").strip() or f"Câu {idx}",
                    content_latex=(q.content_latex or q.content or "").strip() or f"Câu {idx}",
                    options=q.options or [],
                    correct_answer=q.correct_answer,
                    has_image=has_image,
                    image_url=image_url,
                    difficulty_a=q.difficulty_a if q.difficulty_a is not None else 1.0,
                    difficulty_b=q.difficulty_b if q.difficulty_b is not None else 0.0,
                    topic_tags=q.topic_tags or [],
                    max_score=q.max_score,
                )
            )

        exam_doc = ExamDocument(
            id=resolved_exam_id,
            subject=(payload.exam.subject or "Toán").strip() or "Toán",
            exam_type=(payload.exam.exam_type or "PREPROCESS_OCR").strip() or "PREPROCESS_OCR",
            grade=int(payload.exam.grade or 12),
            year=int(payload.exam.year or datetime.now().year),
            source=(payload.exam.source or "OCR_PARSER").strip() or "OCR_PARSER",
            generated=bool(payload.exam.generated),
            total_questions=len(normalized_questions),
            duration=int(payload.exam.duration or 90),
            metadata={
                **(payload.exam.metadata or {}),
                "image_bucket_url": image_bucket_url,
                "from_intent": "PREPROCESS",
            },
            created_at=payload.exam.created_at or now_iso,
            questions=[q.id for q in normalized_questions],
        )
        return PreprocessPayload(exam=exam_doc, questions=normalized_questions)

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

    async def _run_batch_phase(self, state: dict[str, Any], phase: str) -> dict[str, Any]:
        outputs: list[Output] = state["debate_outputs"]

        try:
            llm_batch_size = max(1, int(os.getenv("TEACHER_LLM_BATCH_SIZE", "4")))
        except ValueError:
            llm_batch_size = 4
        try:
            max_question_chars = max(1, int(os.getenv("TEACHER_MAX_QUESTION_CHARS", "700")))
        except ValueError:
            max_question_chars = 700

        def _is_length_error(exc: Exception) -> bool:
            msg = str(exc).lower()
            return (
                "length limit" in msg
                or "maximum context length" in msg
                or "too many tokens" in msg
                or "max_tokens" in msg
            )

        def _compact_question(question: dict[str, Any]) -> dict[str, Any]:
            compact = {
                "id": question.get("id"),
                "question_index": question.get("question_index"),
                "type": question.get("type"),
                "content": question.get("content"),
                "content_latex": question.get("content_latex"),
                "options": question.get("options"),
                "correct_answer": question.get("correct_answer"),
                "has_image": question.get("has_image"),
                "image_url": question.get("image_url"),
                "max_score": question.get("max_score"),
            }
            compact = {k: v for k, v in compact.items() if v not in (None, [], "")}
            return compact or question

        output_by_qid = {o.student_ans.question_id: o for o in outputs}
        completed: dict[str, Output] = {}

        try:
            qids = list(output_by_qid.keys())
            question_docs = await self.get_data(
                "masterthpt",
                "questions",
                query={"id": {"$in": qids}},
                length=max(len(qids), 1),
            )
            question_map = {str(q.get("id")): q for q in question_docs}

            for q in (state.get("questions", []) or []):
                q_dict = q.model_dump() if hasattr(q, "model_dump") else dict(q)
                qid = str(q_dict.get("id") or "")
                if qid and qid not in question_map:
                    question_map[qid] = q_dict

            items: list[dict[str, Any]] = []
            solve_mode = True
            for o in outputs:
                qid = o.student_ans.question_id
                q_payload = _compact_question(question_map.get(qid, {}))
                q_text = json.dumps(q_payload, ensure_ascii=False, default=str)
                if len(q_text) > max_question_chars:
                    q_text = q_text[:max_question_chars] + " ...[truncated]"

                student_answer = (o.student_ans.student_answer or "").strip()
                if student_answer:
                    solve_mode = False

                item = {
                    "question_id": qid,
                    "question": q_text,
                    "student_answer": student_answer,
                }
                if phase == "debate":
                    item["draft_result"] = o.draft_result.model_dump() if o.draft_result else None
                    item["verifier_feedback"] = o.verifier_feedback
                items.append(item)

            if phase == "draft":
                llm = self._llm_draft_batch
            else:
                llm = self._llm_debate_batch

            self.logger.agent_node(
                f"Teacher {phase} batching items={len(items)} llm_batch_size={llm_batch_size} max_q_chars={max_question_chars}"
            )

            async def _run_chunk(chunk_items: list[dict[str, Any]]) -> None:
                batch_input_json = json.dumps(chunk_items, ensure_ascii=False, default=str)
                if phase == "draft":
                    mode_instruction = teacher_draft_mode_instruction(solve_mode)
                    prompt = teacher_batch_draft_prompt(mode_instruction, batch_input_json)
                else:
                    prompt = teacher_batch_debate_prompt(batch_input_json)
                try:
                    batch_result = await asyncio.to_thread(llm.invoke, prompt)
                    by_qid = {r.question_id: r for r in (batch_result.results or [])}

                    for item in chunk_items:
                        qid = item["question_id"]
                        o = output_by_qid[qid]
                        r = by_qid.get(qid)

                        if phase == "draft":
                            if r is None:
                                r = DraftResult(
                                    question_id=qid,
                                    is_correct=False,
                                    score=None,
                                    confidence=0.3,
                                    reasoning="Missing result for this question in the batch output.",
                                    feedback="Teacher fallback: missing result in the batch output.",
                                )
                            r.question_id = qid
                            r.confidence = max(0.0, min(1.0, float(getattr(r, "confidence", 0.5))))
                            completed[qid] = o.model_copy(update={"draft_result": r})
                        else:
                            if r is None:
                                r = DebateResult(
                                    question_id=qid,
                                    teacher_rebuttal="Missing result for this question in the batch output.",
                                    final_feedback="Teacher fallback used due to missing result in the batch output.",
                                    final_score=(o.draft_result.score if o.draft_result else None),
                                    accepted_verifier=False,
                                )
                            r.question_id = qid
                            completed[qid] = o.model_copy(update={"debate_result": r})

                except Exception as exc:
                    if _is_length_error(exc) and len(chunk_items) > 1:
                        mid = len(chunk_items) // 2
                        self.logger.warning(
                            f"Teacher {phase} chunk exceeded model length; splitting chunk "
                            f"size={len(chunk_items)} into {mid} and {len(chunk_items) - mid}"
                        )
                        await _run_chunk(chunk_items[:mid])
                        await _run_chunk(chunk_items[mid:])
                        return

                    self.logger.warning(
                        f"Teacher {phase} chunk failed; using deterministic fallback for "
                        f"{len(chunk_items)} item(s): {exc}"
                    )
                    for item in chunk_items:
                        qid = item["question_id"]
                        o = output_by_qid[qid]
                        if phase == "draft":
                            fallback = DraftResult(
                                question_id=qid,
                                is_correct=False,
                                score=None,
                                confidence=0.2,
                                reasoning="Draft batch failed; generated fallback result.",
                                feedback="Teacher fallback used because the draft batch failed.",
                            )
                            completed[qid] = o.model_copy(update={"draft_result": fallback})
                        else:
                            fallback = DebateResult(
                                question_id=qid,
                                teacher_rebuttal="Debate batch failed; generated fallback result.",
                                final_feedback="Teacher fallback used because the debate batch failed.",
                                final_score=(o.draft_result.score if o.draft_result else None),
                                accepted_verifier=False,
                            )
                            completed[qid] = o.model_copy(update={"debate_result": fallback})

            for i in range(0, len(items), llm_batch_size):
                await _run_chunk(items[i:i + llm_batch_size])
        except Exception as e:
            self.logger.warning(f"Teacher {phase} batch failed, using deterministic fallback: {e}")
            for o in outputs:
                qid = o.student_ans.question_id
                if phase == "draft":
                    fallback = DraftResult(
                        question_id=qid,
                        is_correct=False,
                        score=None,
                        confidence=0.2,
                        reasoning="Draft batch failed; generated fallback result.",
                        feedback="Teacher fallback used because the draft batch failed.",
                    )
                    completed[qid] = o.model_copy(update={"draft_result": fallback})
                else:
                    fallback = DebateResult(
                        question_id=qid,
                        teacher_rebuttal="Debate batch failed; generated fallback result.",
                        final_feedback="Teacher fallback used because the debate batch failed.",
                        final_score=(o.draft_result.score if o.draft_result else None),
                        accepted_verifier=False,
                    )
                    completed[qid] = o.model_copy(update={"debate_result": fallback})

        ordered = [completed[o.student_ans.question_id] for o in outputs]
        next_state = {**state, "debate_outputs": ordered, "phase": "verify"}
        if phase == "debate":
            next_state["round"] = state["round"] + 1
        return next_state

    # ── Draft / Debate Phase ──────────────────────────────────────────────────

    async def _draft_batch(self, state: dict[str, Any]) -> dict[str, Any]:
        return await self._run_batch_phase(state, phase="draft")

    async def _debate_batch(self, state: dict[str, Any]) -> dict[str, Any]:
        return await self._run_batch_phase(state, phase="debate")

    # ── Public API ─────────────────────────────────────────────────────────────

    async def run_draft(
        self,
        state: dict[str, Any],
        thread_id: str = "default",
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
        config = build_langsmith_invoke_config(
            run_name="TeacherAgent.run_draft",
            agent_role="teacher",
            model_name="gemma-4-31B-it",
            thread_id=thread_id,
            extra_tags=["teacher", "draft"],
        )
        result = await self.graph.ainvoke(state, config=config)
        self.logger.agent_node("Teacher run_draft completed")
        return result

    async def run_debate(
        self,
        state: dict[str, Any],
        thread_id: str = "default",
    ) -> dict[str, Any]:
        """Phase 2: Nhận AgentState (đã có verifier_feedback), tranh luận batch."""
        self.logger.agent_node(f"Teacher run_debate called thread_id={thread_id}")
        state = {**state, "phase": "debate"}
        config = build_langsmith_invoke_config(
            run_name="TeacherAgent.run_debate",
            agent_role="teacher",
            model_name="gemma-4-31B-it",
            thread_id=thread_id,
            extra_tags=["teacher", "debate"],
        )
        result = await self.graph.ainvoke(state, config=config)
        self.logger.agent_node("Teacher run_debate completed")
        return result

    async def run_hint(
        self,
        request: MessageRequest,
        exam_id: Optional[str] = None,
    ) -> MessageResponse:
        """ASK_HINT: trả về gợi ý trực tiếp, không đi qua verifier/debate."""
        question_id = request.question_id
        if not question_id and request.student_answers:
            question_id = request.student_answers[0].question_id

        student_answer = None
        if request.student_answers:
            student_answer = request.student_answers[0].student_answer

        if question_id:
            question = await self.get_data(
                "masterthpt", "questions", query={"id": question_id}
            )
        else:
            question = "Không có question_id trong request"

        prompt = teacher_hint_prompt(
            question=question,
            student_answer=student_answer,
            student_message=request.student_message,
        )

        result: HintResult = await asyncio.to_thread(
            self._llm_hint.invoke,
            prompt,
            build_langsmith_invoke_config(
                run_name="TeacherAgent.run_hint",
                agent_role="teacher",
                model_name="gemma-4-31B-it",
                extra_tags=["teacher", "hint"],
                extra_metadata={"question_id": question_id},
            ),
        )
        feedback = (result.feedback or "").strip()
        if not feedback:
            feedback = "Mình cần thêm thông tin để gợi ý chính xác hơn. Bạn hãy gửi cách làm hiện tại của bạn nhé."

        return MessageResponse(
            student_id=request.student_id,
            exam_id=exam_id or request.exam_id,
            question_id=question_id,
            feedback=feedback,
        )

    async def run_preprocess(
        self,
        request: MessageRequest,
        exam_id: Optional[str] = None,
        thread_id: Optional[str] = None,
    ) -> MessageResponse:
        """PREPROCESS: parse OCR text thành payload chuẩn exams/questions để ghi DB."""
        parser_output = (request.parser_output or "").strip()
        image_bucket_url = (
            request.image_bucket_url
            or os.getenv("PARSER_IMAGE_BUCKET_URL")
            or "https://drive.google.com/drive/folders/1ygew6DN6kXgLi0R-0bDQAq8_r0dHai0v?usp=sharing"
        )

        if not parser_output:
            empty_payload = self._fallback_preprocess_payload(
                parser_output="",
                request=request,
                exam_id=exam_id,
                image_bucket_url=image_bucket_url,
            )
            return MessageResponse(
                student_id=request.student_id,
                exam_id=exam_id or request.exam_id,
                question_id=request.question_id,
                feedback="Teacher đã nhận PREPROCESS nhưng parser_output đang rỗng.",
                preprocess_payload=empty_payload,
            )

        prompt = teacher_preprocess_prompt(
            image_bucket_url=image_bucket_url,
            parser_output=parser_output,
        )

        try:
            invoke_kwargs = {}
            if thread_id:
                invoke_kwargs["config"] = {"configurable": {"thread_id": thread_id}}
            extraction: PreprocessExtractionResult = await asyncio.to_thread(
                self._llm_preprocess.invoke,
                prompt,
                **invoke_kwargs,
            )
            normalized_payload = self._normalize_preprocess_payload(
                extraction,
                request=request,
                exam_id=exam_id,
                image_bucket_url=image_bucket_url,
            )
            feedback = (
                "PREPROCESS thành công: đã chuẩn hóa payload để ghi MongoDB "
                f"(exam_id={normalized_payload.exam.id}, questions={len(normalized_payload.questions)})."
            )
        except Exception as e:
            self.logger.warning(f"Teacher preprocess extraction failed, using fallback payload: {e}")
            normalized_payload = self._fallback_preprocess_payload(
                parser_output=parser_output,
                request=request,
                exam_id=exam_id,
                image_bucket_url=image_bucket_url,
            )
            feedback = (
                "PREPROCESS fallback: LLM parsing failed, returned default payload to continue DB persistence. "
                f"Error details: {e}"
            )

        return MessageResponse(
            student_id=request.student_id,
            exam_id=exam_id or request.exam_id,
            question_id=request.question_id,
            feedback=feedback,
            preprocess_payload=normalized_payload,
        )

    async def run(self, input: str) -> str:
        return "Use run_draft() or run_debate() instead."
