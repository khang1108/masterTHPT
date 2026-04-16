"""
Parser Agent — Trích xuất câu trả lời của học sinh từ file bài làm (ảnh, PDF, …).

Luồng hoạt động:
  GRADE_SUBMISSION request  →  parse()  →  VIEW_ANALYSIS request
  (có file_urls)                            (đã có student_answers)

Điểm cốt lõi:
  • Xử lý song song nhiều file bằng asyncio.gather.
  • Mỗi file chạy LLM trong thread riêng qua asyncio.to_thread → tận dụng
    thread pool mặc định của Python (ThreadPoolExecutor) mà không block
    event loop.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Optional

from dotenv import load_dotenv

from master.agents import BaseAgent
from master.agents.common.llm_client import LLMClient
from master.agents.common.message import (
    Intent,
    MessageRequest,
    StudentAnswer,
)

load_dotenv(override=True)

logger = logging.getLogger(__name__)


class ParserAgent(BaseAgent):
    """
    Nhận MessageRequest với intent=GRADE_SUBMISSION, trả về
    MessageRequest với intent=VIEW_ANALYSIS và student_answers đã trích xuất.

    Mỗi file được xử lý độc lập trong thread pool (asyncio.to_thread),
    toàn bộ files chạy song song qua asyncio.gather.
    """

    def __init__(self) -> None:
        super().__init__(agent_role="parser")
        self._llm = None

    # ── Setup ──────────────────────────────────────────────────────────────────

    async def setup(self) -> None:
        """Khởi tạo LLM client."""
        self._llm = LLMClient.chat_model(agent_role="parser")
        logger.info("[parser] setup complete")

    # ── Single-file extraction ─────────────────────────────────────────────────

    async def _extract_from_file(self, file_url: str) -> StudentAnswer:
        """
        Trích xuất StudentAnswer từ một file bài làm.

        Gọi LLM bên trong asyncio.to_thread → chạy trong Python's default
        ThreadPoolExecutor, không block event loop, cho phép nhiều file
        xử lý đồng thời.

        Ghi chú: Kích thước thread pool mặc định có thể tuỳ chỉnh trong
        production bằng loop.set_default_executor(ThreadPoolExecutor(max_workers=N)).
        """
        prompt = (
            f"Từ file bài làm của học sinh tại URL sau, hãy trích xuất thông tin trả lời.\n"
            f"File URL: {file_url}\n\n"
            "Trả về đúng định dạng với các trường:\n"
            "  - question_id: mã câu hỏi (chuỗi, để trống nếu không xác định được)\n"
            "  - answer: câu trả lời của học sinh\n"
            "  - correct_answer: đáp án đúng nếu có trong file, để trống nếu không có\n"
            "Nếu không thể xác định, để trống."
        )

        structured_llm = self._llm.with_structured_output(StudentAnswer)
        student_ans: StudentAnswer = await asyncio.to_thread(
            structured_llm.invoke, prompt
        )
        student_ans.file_urls = [file_url]
        return student_ans

    # ── Public API ─────────────────────────────────────────────────────────────

    async def parse(self, request: MessageRequest) -> MessageRequest:
        """
        Xử lý request GRADE_SUBMISSION → VIEW_ANALYSIS:

        1. Thu thập danh sách file URLs từ request.file_urls hoặc request.metadata.
        2. Xử lý song song tất cả files (asyncio.gather + asyncio.to_thread).
        3. Trả về MessageRequest mới với intent=VIEW_ANALYSIS và metadata
           tương thích với TeacherAgent.ViewAnalysisMeta.

        Parser có thể chạy thread pool vì mỗi lời gọi LLM được bao bọc
        trong asyncio.to_thread, tận dụng ThreadPoolExecutor.
        """
        # Collect file URLs
        file_urls: list[str] = list(request.file_urls or [])
        if not file_urls and request.metadata:
            file_urls = list(request.metadata.get("file_urls", []))

        if not file_urls:
            logger.warning("[parser] No file_urls found in request — returning as-is")
            return request

        logger.info(f"[parser] Processing {len(file_urls)} file(s) in parallel")

        # ── Parallel extraction via thread pool ────────────────────────────────
        student_answers: list[StudentAnswer] = list(
            await asyncio.gather(
                *[self._extract_from_file(url) for url in file_urls]
            )
        )

        logger.info(f"[parser] Extracted {len(student_answers)} student answer(s)")

        # Build metadata dict compatible with TeacherAgent.ViewAnalysisMeta
        existing_meta: dict = dict(request.metadata or {})
        session_id: str = existing_meta.get("session_id") or str(uuid.uuid4())
        exam_id: str = request.exam_id or existing_meta.get("exam_id", "")

        metadata = {
            **existing_meta,
            "exam_id": exam_id,
            "student_id": request.student_id,
            "session_id": session_id,
            "total_questions": len(student_answers),
            "exam_sections": existing_meta.get("exam_sections", []),
            "student_answers": [sa.model_dump() for sa in student_answers],
        }

        return MessageRequest(
            intent=Intent.VIEW_ANALYSIS,
            student_id=request.student_id,
            exam_id=exam_id,
            user_message=request.user_message if request.user_message is not None else request.student_message,
            metadata=metadata,
        )

    async def run(self, input: str) -> str:
        """BaseAgent shim — use parse(MessageRequest) instead."""
        return "Use parse(MessageRequest) to process GRADE_SUBMISSION requests."
