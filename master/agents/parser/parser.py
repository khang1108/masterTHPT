from typing import Optional
from master.agents import BaseAgent
from master.agents.common.tools import ToolsRegistry
from master.agents.common.message import Intent, MessageRequest
from master.agents.common.state import AgentState
from master.agents.common.llm_client import LLMClient
from PIL import Image
import fitz
import io
import re
import base64
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed

from langchain_core.messages import HumanMessage

# OCR config
MAX_OCR_WIDTH = 1240
MAX_OCR_HEIGHT = 1754
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}
DEFAULT_IMAGE_BUCKET_URL = os.getenv("PARSER_IMAGE_BUCKET_URL")
DEFAULT_PARSER_BATCH_SIZE = max(1, int(os.getenv("PARSER_BATCH_SIZE", "2")))


class ParserAgent(ToolsRegistry, BaseAgent):

    def __init__(self):
        super().__init__(agent_role="Parser")
        self._ocr_llm = None

    async def setup(self):
        self.logger.agent_node("Parser setup started")
        self._ensure_ocr_llm()
        self.logger.agent_node("Parser setup completed")

    def _ensure_ocr_llm(self):
        if self._ocr_llm is None:
            self._ocr_llm = LLMClient.chat_model(
                provider="openai_compatible",
                base_url=os.getenv("FPT_BASE_URL"),
                api_key=os.getenv("FPT_API_KEY"),
                model=os.getenv("PARSER_OCR_MODEL", os.getenv("LLM_MODEL", "gemma-4-31B-it")),
                temperature=0.0,
            )
        return self._ocr_llm

    def _load_page_payloads(self, file_path: str) -> tuple[str, list[tuple[int, bytes, str]]]:
        ext = os.path.splitext(file_path)[1].lower()
        source_type = "pdf" if ext == ".pdf" else "image"

        if source_type == "pdf":
            zoom = 300 / 72.0
            matrix = fitz.Matrix(zoom, zoom)
            doc = fitz.open(file_path)
            payloads: list[tuple[int, bytes, str]] = []
            for page_num in range(doc.page_count):
                page = doc.load_page(page_num)
                pix = page.get_pixmap(matrix=matrix, alpha=False)
                payloads.append((page_num + 1, pix.tobytes("png"), f"page_{page_num + 1:03d}.png"))
            doc.close()
            return source_type, payloads

        with open(file_path, "rb") as f:
            raw_bytes = f.read()
        return source_type, [(1, raw_bytes, os.path.basename(file_path))]

    def _ocr_page(self, image_bytes: bytes, image_name: str) -> str:
        llm = self._ensure_ocr_llm()

        try:
            with Image.open(io.BytesIO(image_bytes)) as img:
                w, h = img.size
                if w > MAX_OCR_WIDTH or h > MAX_OCR_HEIGHT:
                    scale = min(MAX_OCR_WIDTH / w, MAX_OCR_HEIGHT / h)
                    img = img.convert("RGB").resize((int(w * scale), int(h * scale)), Image.LANCZOS)
                elif img.mode != "RGB":
                    img = img.convert("RGB")
                out = io.BytesIO()
                img.save(out, format="PNG", optimize=True)
                image_bytes = out.getvalue()
        except Exception:
            pass

        message = HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": (
                        "Bạn là OCR engine. Hãy đọc toàn bộ văn bản trong ảnh và trả về duy nhất nội dung văn bản "
                        "đã OCR theo thứ tự đọc từ trên xuống dưới, trái sang phải. "
                        "Không giải thích, không thêm nhận xét, không bổ sung nội dung ngoài ảnh. "
                        "Giữ nguyên tiếng Việt có dấu và xuống dòng hợp lý."
                    ),
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{base64.b64encode(image_bytes).decode('utf-8')}"
                    },
                },
            ]
        )

        response = llm.invoke([message])
        content = getattr(response, "content", "")
        if isinstance(content, str):
            text = content
        elif isinstance(content, list):
            chunks: list[str] = []
            for item in content:
                if isinstance(item, dict):
                    txt = item.get("text")
                    if txt:
                        chunks.append(str(txt))
                else:
                    chunks.append(str(item))
            text = "\n".join(chunks)
        else:
            text = str(content)

        text = re.sub(r"^```(?:text|markdown)?\s*", "", text.strip())
        text = re.sub(r"\s*```$", "", text).strip()
        if not text:
            raise RuntimeError(f"Qwen OCR tra ve rong cho {image_name}")
        return text

    def ocr_to_text(self, file_path: str, batch_size: Optional[int] = None) -> Optional[str]:
        if not os.path.exists(file_path):
            self.logger.warning(f"Parser input file not found: {file_path}")
            return None

        ext = os.path.splitext(file_path)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            self.logger.warning(f"Parser input extension not supported: {ext}")
            return None

        source_type = "pdf" if ext == ".pdf" else "image"
        self.logger.agent_node(
            f"Parser OCR source={source_type} file={os.path.basename(file_path)}"
        )

        _, page_payloads = self._load_page_payloads(file_path)

        effective_batch_size = max(1, int(batch_size or DEFAULT_PARSER_BATCH_SIZE))
        total_pages = len(page_payloads)
        total_batches = (total_pages + effective_batch_size - 1) // effective_batch_size
        self.logger.agent_node(
            f"Parser OCR batching configured batch_size={effective_batch_size} total_pages={total_pages}"
        )

        pages_text: list[str] = []
        completed_pages = 0
        for batch_start in range(0, total_pages, effective_batch_size):
            batch = page_payloads[batch_start: batch_start + effective_batch_size]
            batch_index = (batch_start // effective_batch_size) + 1
            batch_page_nums = [p[0] for p in batch]
            self.logger.agent_node(
                f"Parser OCR batch {batch_index}/{total_batches} started pages={batch_page_nums}"
            )

            batch_results: dict[int, str] = {}
            with ThreadPoolExecutor(max_workers=effective_batch_size) as executor:
                future_map = {
                    executor.submit(self._ocr_page, image_bytes, image_name): page_num
                    for page_num, image_bytes, image_name in batch
                }

                for future in as_completed(future_map):
                    page_num = future_map[future]
                    try:
                        page_text = future.result()
                        if page_text:
                            batch_results[page_num] = page_text
                        completed_pages += 1
                        self.logger.agent_node(
                            f"Parser OCR page done page={page_num} progress={completed_pages}/{total_pages}"
                        )
                    except Exception as e:
                        completed_pages += 1
                        self.logger.warning(f"Parser OCR failed page={page_num}: {e}")
                        self.logger.agent_node(
                            f"Parser OCR page failed page={page_num} progress={completed_pages}/{total_pages}"
                        )

            for page_num, _, _ in batch:
                page_text = batch_results.get(page_num)
                if page_text:
                    pages_text.append(f"=== PAGE {page_num} ===\n{page_text}")

            self.logger.agent_node(
                f"Parser OCR batch {batch_index}/{total_batches} completed success={len(batch_results)}/{len(batch)}"
            )

        if not pages_text:
            self.logger.warning("Parser OCR produced empty output")
            return None

        parser_output = "\n\n".join(pages_text)
        return parser_output

    @staticmethod
    def build_preprocess_request(
        parser_output: str,
        student_id: str,
        exam_id: Optional[str] = None,
        image_bucket_url: Optional[str] = None,
    ) -> MessageRequest:
        return MessageRequest(
            intent=Intent.PREPROCESS,
            student_id=student_id,
            exam_id=exam_id,
            parser_output=parser_output,
            image_bucket_url=image_bucket_url or DEFAULT_IMAGE_BUCKET_URL,
        )

    @staticmethod
    def build_agent_state(request: MessageRequest) -> AgentState:
        return AgentState(
            request=request,
            learner_profile=None,
            exam_id=request.exam_id,
            questions=[],
            student_answers=request.student_answers or [],
            raw_request=request,
            round=0,
            max_round=0,
            phase="finalize",
            debate_outputs=[],
            grade_result=None,
            solutions=None,
            verified_solutions=None,
            selected_questions=None,
            profile_updates=None,
            response=None,
        )

    async def process(
        self,
        file_path: str,
        student_id: str = "parser",
        exam_id: Optional[str] = None,
        batch_size: Optional[int] = None,
    ) -> Optional[MessageRequest]:
        effective_batch_size = max(1, int(batch_size or DEFAULT_PARSER_BATCH_SIZE))
        self.logger.agent_node(
            f"Parser process started file_path={file_path} batch_size={effective_batch_size}"
        )
        parser_output = self.ocr_to_text(file_path, batch_size=effective_batch_size)
        if not parser_output:
            self.logger.agent_node("Parser process completed with empty parser_output")
            return None

        request = self.build_preprocess_request(
            parser_output=parser_output,
            student_id=student_id,
            exam_id=exam_id,
            image_bucket_url=DEFAULT_IMAGE_BUCKET_URL,
        )
        self.logger.agent_node(
            f"Parser process completed parser_output_len={len(parser_output)}"
        )
        return request

    async def process_to_state(
        self,
        file_path: str,
        student_id: str = "parser",
        exam_id: Optional[str] = None,
        batch_size: Optional[int] = None,
    ) -> Optional[AgentState]:
        request = await self.process(
            file_path=file_path,
            student_id=student_id,
            exam_id=exam_id,
            batch_size=batch_size,
        )
        if request is None:
            return None
        return self.build_agent_state(request)

    async def run(self, input: str) -> str:
        """BaseAgent interface: nhận đường dẫn file và trả OCR text."""
        self.logger.agent_node(
            f"Parser run started input={input} batch_size={DEFAULT_PARSER_BATCH_SIZE}"
        )
        result = self.ocr_to_text(input, batch_size=DEFAULT_PARSER_BATCH_SIZE)
        self.logger.agent_node(
            f"Parser run completed parser_output_len={len(result) if result else 0}"
        )
        return result or ""


def process_sync(
    file_path: str,
    student_id: str = "parser",
    exam_id: Optional[str] = None,
    batch_size: Optional[int] = None,
) -> Optional[MessageRequest]:
    parser = ParserAgent()
    return asyncio.run(
        parser.process(
            file_path=file_path,
            student_id=student_id,
            exam_id=exam_id,
            batch_size=batch_size,
        )
    )
