from accelerate.utils import transformer_engine
from typing import Optional
from langchain_core.messages import HumanMessage, SystemMessage
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image, ImageDraw, ImageFont, ImageStat
from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator

from master.agents import BaseAgent
from master.agents.common.tools import ToolsRegistry
from master.agents.common.message import Intent, MessageRequest, ExamDocument
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

class Type(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_ans"

class QuestionOutput(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question_index: int = Field(description="Số thứ tự câu hỏi trong đề, bắt đầu từ 1")
    type: Type = Field(description="Loại câu hỏi, là 1 trong 3 loại sau 'multiple_choice' hoặc 'true_false' hoặc 'short_ans'")
    content: str = Field(description="Nội dung câu hỏi, có thể bao gồm cả text và LaTeX, bỏ phần đầu như 'Câu 1: ' hoặc '1.")
    options: Optional[list[str]] = Field(default=None, description="Danh sách lựa chọn nếu là câu hỏi trắc nghiệm, để trống nếu là câu hỏi tự luận")
    has_image: bool = Field(description="Câu hỏi có chứa hình ảnh hay không")
    image_url: Optional[str] = Field(default=None, description="URL của hình ảnh nếu có")


    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        content = value.strip()
        if not content:
            raise ValueError("content must not be empty")
        return content

    @field_validator("options")
    @classmethod
    def validate_options_items(cls, value: Optional[list[str]]) -> Optional[list[str]]:
        if value is None:
            return None

        normalized_options = [str(option).strip() for option in value if str(option).strip()]
        return normalized_options or None

    @model_validator(mode="after")
    def validate_question_rules(self) -> "QuestionOutput":
        if self.type == Type.MULTIPLE_CHOICE:
            if not self.options or len(self.options) != 4:
                raise ValueError("multiple_choice must have exactly 4 options")

            expected_prefixes = ("A.", "B.", "C.", "D.")
            all_correct = all(
                option.startswith(prefix)
                for option, prefix in zip(self.options, expected_prefixes)
            )

            if not all_correct:
                # Normalize: strip existing wrong prefixes and add correct ones
                normalized = []
                for option, prefix in zip(self.options, expected_prefixes):
                    text = option.strip()
                    # Remove existing prefix patterns like "a.", "a)", "A)", "1.", etc.
                    text = re.sub(r"^[A-Da-d1-4][.\)]\s*", "", text).strip()
                    normalized.append(f"{prefix} {text}")
                self.options = normalized

        elif self.type == Type.TRUE_FALSE:
            if not self.options:
                raise ValueError("true_false must have options")

            expected_prefixes = list("abcd")[:len(self.options)]
            normalized = []
            for option, letter in zip(self.options, expected_prefixes):
                text = option.strip()
                if re.match(r"^[a-d][.\)]", text):
                    normalized.append(text)
                else:
                    # Remove wrong prefix and add correct one
                    text = re.sub(r"^[A-Da-d1-4][.\)]\s*", "", text).strip()
                    normalized.append(f"{letter}) {text}")
            self.options = normalized

        elif self.type == Type.SHORT_ANSWER:
            if self.options is not None:
                raise ValueError("short_ans must have options = []")

        return self


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

    def _extract_options_from_content(self, content: str, options: list | None) -> tuple[str, list[str]]:
        """
        Normalize true_false questions where options (a), b), c), d)) are
        embedded in the content field instead of in the options array.
        
        Returns (cleaned_content, extracted_options).
        """
        # If options already exist and are non-empty, no extraction needed
        if options:
            return content, options

        # Pattern to match lines starting with a), b), c), d) or a., b., c., d.
        # These are typical true_false sub-option prefixes
        option_pattern = re.compile(
            r"^[ \t]*([a-d][\.\)])\s*(.+)",
            re.IGNORECASE | re.MULTILINE
        )

        matches = list(option_pattern.finditer(content))
        if len(matches) < 2:
            # Need at least 2 sub-options to consider them as embedded options
            return content, options or []

        # Verify the prefixes are sequential (a, b, c, d order)
        found_prefixes = [m.group(1)[0].lower() for m in matches]
        expected = list("abcd")[:len(found_prefixes)]
        if found_prefixes != expected:
            return content, options or []

        # Extract full option text for each match (from prefix to next match or end)
        extracted_options: list[str] = []
        for idx, match in enumerate(matches):
            start = match.start()
            end = matches[idx + 1].start() if idx + 1 < len(matches) else len(content)
            option_text = content[start:end].strip()
            extracted_options.append(option_text)

        # Clean content: remove the options portion
        first_option_start = matches[0].start()
        cleaned_content = content[:first_option_start].strip()

        self.logger.agent_node(
            f"Parser extracted {len(extracted_options)} options from content for true_false question"
        )
        return cleaned_content, extracted_options

    def _normalize_question_type(self, raw_type: str | None, options: list | None) -> Type:
        """
        Determine question type. Options prefix casing takes priority over raw_type
        because OCR can mislabel types:
        - Uppercase A., B., C., D. -> multiple_choice
        - Lowercase a., b., c., d. or a), b), c), d) -> true_false
        """
        # Check options prefix casing first to detect the actual type
        if options and len(options) >= 2:
            has_uppercase = all(
                isinstance(opt, str) and re.match(r'^[A-D]\.', opt.strip())
                for opt in options
            )
            has_lowercase = all(
                isinstance(opt, str) and re.match(r'^[a-d][.)]', opt.strip())
                for opt in options
            )
            if has_uppercase and len(options) == 4:
                return Type.MULTIPLE_CHOICE
            if has_lowercase:
                return Type.TRUE_FALSE

        # Fall back to raw_type from OCR
        if raw_type:
            raw = str(raw_type).strip().lower()
            if raw in {"short_ans", "short_answer", "tự luận", "tu luan"}:
                return Type.SHORT_ANSWER
            if raw in {"multiple_choice", "multiple choice", "trắc nghiệm", "trac nghiem"}:
                return Type.MULTIPLE_CHOICE
            if raw in {"true_false", "true false", "đúng sai", "đúng/sai", "dung sai"}:
                return Type.TRUE_FALSE
            try:
                return Type(raw)
            except ValueError:
                pass

        # Last resort heuristics
        if not options or len(options) == 0:
            return Type.SHORT_ANSWER

        return Type.MULTIPLE_CHOICE


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

        result = self._llm.invoke(self.build_messages(message))
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

        # Save ocr_pages to JSON for debugging
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
        question_index = 0

        for page in ocr_pages:
            page_questions: list[dict] = []

            if isinstance(page, dict) and isinstance(page.get("questions"), list):
                page_questions = [q for q in page["questions"] if isinstance(q, dict)]
            elif isinstance(page, dict) and "content" in page:
                page_questions = [page]
            elif isinstance(page, dict) and "raw_text" in page:
                page_questions = [{"content": page.get("raw_text", "")}]

            for item in page_questions:
                question_index += 1

                # Get question content and normalize it to remove text like 'Câu 1:'
                content = str(item.get("content", "")).strip()
                content = re.sub(r"^Câu\s*\d+\s*[:.\-]?\s*", "", content, flags=re.IGNORECASE).strip()
                if not content:
                    question_index -= 1
                    continue

                # Check if question has image and get image URL if available
                image_url = item.get("image_url")
                has_image = bool(item.get("has_image"))
                if not has_image:
                    lower_content = content.lower()
                    has_image = bool(image_url) or "![" in content or "<img" in lower_content
                
                # Extract options if it's a multiple choice question
                options = item.get("options", [])
                
                # Normalize: extract options embedded in content for true_false questions
                raw_type = item.get("type", "")
                raw_type_lower = str(raw_type).strip().lower() if raw_type else ""
                if raw_type_lower in {"true_false", "true false", "đúng sai", "đúng/sai", "dung sai"} or not options:
                    content, options = self._extract_options_from_content(content, options)

                # Get the type of the question
                question_type = self._normalize_question_type(item.get("type"), options)

                # Create question output object
                try:
                    question_obj = QuestionOutput(
                        question_index=question_index,
                        type=question_type,
                        options=options if options else None,
                        content=content,
                        has_image=has_image,
                        image_url=image_url if has_image else None,
                    )
                except ValidationError as error:
                    self.logger.warning(
                        f"Parser question validation failed at index={question_index}: {error}"
                    )
                    continue

                # Add question object to the list
                questions.append(question_obj)

        exam = ExamDocument.model_validate({
            "id": str(uuid.uuid4()),
            "subject": metadata.subject or "Toán",
            "exam_type": metadata.exam_type or "PREPROCESS_OCR",
            "year": metadata.year or datetime.datetime.now().year,
            "grade": metadata.grade or 12,
            "source": metadata.source or "OCR_PARSER",
            "generated": metadata.generated,
            "total_questions": len(questions),
            "duration": metadata.duration or 90,
            "created_at": datetime.datetime.now().isoformat(),
            "questions": [q.id for q in questions],
        })

        parser_output = {"questions": [q.model_dump() for q in questions]}

        # output_path = "ocr_output.json"
        # with open(output_path, "w", encoding="utf-8") as file:
        #     json.dump(parser_output, file, ensure_ascii=False, indent=2)
        # self.logger.agent_node(f"Parser saved parsed OCR output to {output_path}")
        
        await self.insert_data("masterthpt", "exams", [exam.model_dump(mode="json")])
        self.logger.agent_node(f"Parser saved exam with {len(questions)} questions to database")
        
        return parser_output
    
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