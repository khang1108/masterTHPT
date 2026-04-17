from accelerate.utils import transformer_engine
from typing import Optional
from langchain_core.messages import HumanMessage
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image, ImageDraw, ImageFont, ImageStat
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from master.agents import BaseAgent
from master.agents.common.tools import ToolsRegistry
from master.agents.common.message import Intent, MessageRequest
from master.agents.common.state import AgentState
from master.agents.common.llm_client import LLMClient
from master.agents.common.prompt import parser_ocr_instruction

import requests
import asyncio
import base64
import json
import uuid
import fitz
import io
import re
import os


# OCR config
MAX_OCR_WIDTH = 1240
MAX_OCR_HEIGHT = 1754
MIN_GRAYSCALE_RANGE = 10
WHITE_PIXEL_THRESHOLD = 247
MIN_NON_WHITE_RATIO = 0.003

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}
PARSER_IMAGE_BUCKET_URL = os.getenv("PARSER_IMAGE_BUCKET_URL")

load_dotenv(override=True)


class OCROutput(BaseModel):
    id: Optional[str] = None
    type: str = Field(description="Loại câu hỏi, có thể là 'multiple_choice' hoặc 'true_false' hoặc 'short_ans'")
    content: str = Field(description="Đề bài thuần văn bản, có thể bao gồm cả LaTeX nhưng không bao gồm hình ảnh. Nếu đề bài có hình ảnh thì phần content chỉ cần mô tả ngắn gọn về hình ảnh đó.")
    options: list[str] = Field(default_factory=list)


class ParserAgent(ToolsRegistry, BaseAgent):

    def __init__(self):
        super().__init__(agent_role="Parser")
        self._llm = None
        self._llm_with_output = None

    async def setup(self):
        if self._llm is None:
            self._llm = LLMClient.chat_model(
                provider="openai_compatible",
                base_url=os.getenv("FPT_BASE_URL"),
                api_key=os.getenv("FPT_API_KEY"),
                model="Qwen2.5-VL-7B-Instruct",
            )
            self._llm_with_output = self._llm.with_structured_output(OCROutput)

    def _load_file(self, file_path: str) -> tuple[str, list[tuple[int, bytes, str]]]:
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

    # ── Preprocess ──────────────────────────────────────────────────────────────

    def _resize_image(self, image_bytes: bytes) -> bytes:
        try:
            with Image.open(io.BytesIO(image_bytes)) as image:
                w, h = image.size
                if w > MAX_OCR_WIDTH or h > MAX_OCR_HEIGHT:
                    scale = min(MAX_OCR_WIDTH / w, MAX_OCR_HEIGHT / h)
                    image = image.convert("RGB").resize(
                        (int(w * scale), int(h * scale)), Image.LANCZOS
                    )
                elif image.mode != "RGB":
                    image = image.convert("RGB")
                out = io.BytesIO()
                image.save(out, format="PNG", optimize=True)
                return out.getvalue()
        except Exception:
            pass
        return image_bytes

    def _drop_white_page(self, image_bytes: bytes) -> bool:
        try:
            with Image.open(io.BytesIO(image_bytes)) as image:
                grayscale = image.convert("L")
                stats = ImageStat.Stat(grayscale)
                min_pixel, max_pixel = stats.extrema[0]

                if (
                    max_pixel - min_pixel < MIN_GRAYSCALE_RANGE
                    and stats.mean[0] >= WHITE_PIXEL_THRESHOLD
                ):
                    return False

                pixels = list(grayscale.getdata())
                total_pixels = max(1, len(pixels))
                non_white_pixels = sum(pixel < WHITE_PIXEL_THRESHOLD for pixel in pixels)
                return (non_white_pixels / total_pixels) >= MIN_NON_WHITE_RATIO
        except Exception as error:
            self.logger.error(f"Drop white page failed: {error}")
            return False

    # ── OCR ─────────────────────────────────────────────────────────────────────

    def _ocr_single_page(self, image_bytes: bytes, image_name: str) -> OCROutput:
        """OCR một trang và trả về OCROutput đã ép kiểu."""
        message = HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": parser_ocr_instruction()
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{base64.b64encode(image_bytes).decode('utf-8')}"
                    },
                },
            ]
        )

        result: OCROutput = self._llm_with_output.invoke([message])
        # Gán id tự động nếu model không trả về
        if not result.id:
            result.id = uuid.uuid4().hex[:8]
        return result

    # ── Run Batch OCR ────────────────────────────────────────────────────────────

    def _ocr_file(self, file_path: str, batch_size: Optional[int] = None) -> list[OCROutput]:
        """OCR toàn bộ file, trả về danh sách OCROutput theo thứ tự trang."""
        if not os.path.exists(file_path):
            self.logger.warning(f"Parser input file not found: {file_path}")
            return []

        extension = os.path.splitext(file_path)[1].lower()
        if extension not in ALLOWED_EXTENSIONS:
            self.logger.warning(f"Parser input extension not supported: {extension}")
            return []

        source_type, page_payloads = self._load_file(file_path)
        total_pages = len(page_payloads)
        total_batches = (total_pages + batch_size - 1) // batch_size

        # Lưu kết quả theo page_num để giữ đúng thứ tự
        all_results: dict[int, OCROutput] = {}
        completed_pages = 0

        for i in range(0, total_pages, batch_size):
            batch = page_payloads[i: i + batch_size]
            batch_index = (i // batch_size) + 1
            batch_page_nums = [page[0] for page in batch]

            self.logger.agent_node(
                f"Parser OCR batch {batch_index}/{total_batches} started pages={batch_page_nums}"
            )

            with ThreadPoolExecutor(max_workers=batch_size) as executor:
                future_map = {
                    executor.submit(self._ocr_single_page, image_bytes, image_name): page_num
                    for page_num, image_bytes, image_name in batch
                    if self._drop_white_page(image_bytes)
                }

                for future in as_completed(future_map):
                    page_num = future_map[future]
                    try:
                        ocr_output: OCROutput = future.result()
                        all_results[page_num] = ocr_output
                        completed_pages += 1
                        self.logger.agent_node(
                            f"Parser OCR page done page={page_num} "
                            f"progress={completed_pages}/{total_pages}"
                        )
                    except Exception as e:
                        completed_pages += 1
                        self.logger.warning(f"Parser OCR failed page={page_num}: {e}")

            self.logger.agent_node(
                f"Parser OCR batch {batch_index}/{total_batches} completed pages={batch_page_nums}"
            )

        # Trả về danh sách sắp xếp theo thứ tự trang
        return [all_results[page_num] for page_num in sorted(all_results.keys())]

    async def run(self, input: str) -> str:
        pass


if __name__ == "__main__":
    agent = ParserAgent()
    asyncio.run(agent.setup())

    file = "c:\\Users\\abcsd\\Downloads\\test.pdf"
    questions: list[OCROutput] = agent._ocr_file(file, batch_size=2)

    output_path = "ocr_output.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(
            [q.model_dump() for q in questions],
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(f"Saved {len(questions)} questions to {output_path}")