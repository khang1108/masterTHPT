from accelerate.utils import transformer_engine
from typing import Optional
from langchain_core.messages import HumanMessage
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image, ImageDraw, ImageFont, ImageStat
from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError

from master.agents import BaseAgent
from master.agents.common.tools import ToolsRegistry
from master.agents.common.message import Intent, MessageRequest
from master.agents.common.state import AgentState
from master.agents.common.llm_client import LLMClient
from master.agents.common.prompt import parser_ocr_instruction, parser_system_prompt

import datetime
import requests
import asyncio
import base64
import uuid
import json
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

class QuestionOutput(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question_index: int = Field(description="Số thứ tự câu hỏi trong đề, bắt đầu từ 1")
    type: str = Field(description="Loại câu hỏi, là 1 trong 3 loại sau 'multiple_choice' hoặc 'true_false' hoặc 'short_ans'")
    content: str = Field(description="Nội dung câu hỏi, có thể bao gồm cả text và LaTeX")
    options: Optional[list[str]] = Field(default=None, description="Danh sách lựa chọn nếu là câu hỏi trắc nghiệm, để trống nếu là câu hỏi tự luận")
    has_image: bool = Field(description="Câu hỏi có chứa hình ảnh hay không")
    image_url: Optional[str] = Field(default=None, description="URL của hình ảnh nếu có")


class OCRMetadataOutput(BaseModel):
    subject: Optional[str] = None
    exam_type: Optional[str] = None
    year: Optional[int] = None
    grade: Optional[int] = None
    source: Optional[str] = None
    total_questions: Optional[int] = None
    duration: Optional[int] = None
    generated: bool = Field(default=False, description="True nếu metadata được tạo ra bởi LLM, False nếu được trích xuất trực tiếp từ đề thi. Nếu generated = True thì các trường có thể không chính xác và chỉ mang tính tham khảo.")
    

class ParserAgent(ToolsRegistry, BaseAgent):

    def __init__(self):
        super().__init__(agent_role="Parser")
        self.system_prompt = parser_system_prompt()
        self._llm = None
        self._llm_with_output = None

    async def setup(self):
        self.logger.agent_node("Parser setup started")
        llm = LLMClient.chat_model(
            provider="openai_compatible",
            base_url=os.getenv("FPT_BASE_URL"),
            api_key=os.getenv("FPT_API_KEY"),
            model="gemma-4-31B-it",
            temperature=0.1,
            top_p=0.8,
            max_tokens=4096,
        )
        self._llm = llm
        self.logger.agent_node("Parser setup completed")


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

                pixels = list(grayscale.get_flattened_data())
                total_pixels = max(1, len(pixels))
                non_white_pixels = sum(pixel < WHITE_PIXEL_THRESHOLD for pixel in pixels)
                return (non_white_pixels / total_pixels) >= MIN_NON_WHITE_RATIO
        except Exception as error:
            self.logger.error(f"Drop white page failed: {error}")
            return False

    # ── OCR ─────────────────────────────────────────────────────────────────────

    def _ocr_single_page(self, image_bytes: bytes, image_name: str) -> dict:
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

        result = self._llm.invoke([message])
        content = result.content if hasattr(result, "content") else result

        if isinstance(content, list):
            raw = "".join(
                chunk.get("text", "") if isinstance(chunk, dict) else str(chunk)
                for chunk in content
            )
        else:
            raw = str(content)

        clean = raw.strip()
        clean = re.sub(r"^```json\s*", "", clean)
        clean = re.sub(r"\s*```$", "", clean)
        
        try:
            return json.loads(clean)
        except json.JSONDecodeError:
            return {"raw_text": clean}

    # ── Run Batch OCR ────────────────────────────────────────────────────────────

    async def _ocr_file(self, file_path: str, batch_size: Optional[int] = None) -> list[dict]:
        if not os.path.exists(file_path):
            self.logger.warning(f"Parser input file not found: {file_path}")
            return []

        extension = os.path.splitext(file_path)[1].lower()
        if extension not in ALLOWED_EXTENSIONS:
            self.logger.warning(f"Parser input extension not supported: {extension}")
            return []

        if not batch_size or batch_size <= 0:
            batch_size = 2

        _, page_payloads = self._load_file(file_path)
        total_pages = len(page_payloads)
        total_batches = (total_pages + batch_size - 1) // batch_size

        all_results: dict[int, dict] = {}
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
                        ocr_output = future.result()
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

        # Sort results by page number to ensure correct order
        ocr_pages = [all_results[page_num] for page_num in sorted(all_results.keys())]

        # # Save ocr_pages to JSON for debugging
        # debug_output_path = f"ocr_output.json"
        # with open(debug_output_path, "w", encoding="utf-8") as f:
        #     json.dump(ocr_pages, f, ensure_ascii=False, indent=2)
            
        raw_metadata = ocr_pages[0].get("metadata", {}) if ocr_pages else {}
        try:
            metadata = OCRMetadataOutput.model_validate(
                raw_metadata if isinstance(raw_metadata, dict) else {}
            )
        except ValidationError as error:
            self.logger.warning(f"Parser metadata validation failed: {error}")
            metadata = OCRMetadataOutput()

        questions: list[QuestionOutput] = []
        question_index = 1

        for page in ocr_pages:
            page_questions: list[dict] = []

            if isinstance(page, dict) and isinstance(page.get("questions"), list):
                page_questions = [q for q in page["questions"] if isinstance(q, dict)]
            elif isinstance(page, dict) and "content" in page:
                page_questions = [page]
            elif isinstance(page, dict) and "raw_text" in page:
                page_questions = [{"content": page.get("raw_text", "")}]

            for item in page_questions:
                # Get question content and check if it's valid
                content = str(item.get("content", "")).strip()
                if not content:
                    continue

                # Check if question has image and get image URL if available
                image_url = item.get("image_url")
                has_image = bool(item.get("has_image"))
                if not has_image:
                    lower_content = content.lower()
                    has_image = bool(image_url) or "![" in content or "<img" in lower_content
                
                # Extract options if it's a multiple choice question
                options = item.get("options", [])
                
                # Get the type of the question
                types = item.get("type", "multiple_choice")

                # Create question output object
                question_obj = QuestionOutput(
                    question_index=question_index,
                    type=types,
                    options=options if options else None,
                    content=content,
                    has_image=has_image,
                    image_url=image_url if has_image else None,
                )

                # Add question object to the list
                questions.append(question_obj)
                question_index += 1

        exam = {
            "id": str(uuid.uuid4()),
            "subject": metadata.subject,
            "exam_type": metadata.exam_type,
            "year": metadata.year,
            "grade": metadata.grade,
            "source": metadata.source,
            "total_questions": len(questions),
            "duration": metadata.duration,
            "created_at": datetime.datetime.now().isoformat(),
            "questions": [q.id for q in questions],
        }

        await self.insert_data("masterthpt", "exams", [exam])
        self.logger.agent_node(f"Parser saved exam with {len(questions)} questions to database")
        
        return {"questions": [q.model_dump() for q in questions]}
    
    async def parser(self, state: AgentState) -> AgentState:
        request = state["request"]
        file_path = request.file_path
        if not file_path:
            self.logger.warning("Parser request missing file_path in parser_output")
            
            return AgentState(request=request)

        questions = await self._ocr_file(file_path, batch_size=2)
        self.logger.agent_node(f"Parser extracted {len(questions.get('questions', []))} questions from file")
        request = MessageRequest(
            intent=request.intent,
            student_id=request.student_id,
            question_id=request.question_id,
            parser_output=questions.get("questions", []),
        )

        return AgentState(request=request)
    
    def parser_router(self, state: AgentState) -> str:
        requests = state["request"]
        intetnt = requests.intent
        if intetnt == Intent.PREPROCESS.value:
            return "parser"
        else:
            return "teacher"


    async def run(self, input: str) -> str:
        pass


if __name__ == "__main__":
    agent = ParserAgent()
    asyncio.run(agent.setup())

    file = "c:\\Users\\abcsd\\Downloads\\test.pdf"
    questions: list[dict] = asyncio.run(agent._ocr_file(file, batch_size=2))

    output_path = "ocr_output_tune.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(questions)} questions to {output_path}")