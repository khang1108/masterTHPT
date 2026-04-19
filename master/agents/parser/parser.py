from typing import Optional
from langchain_core.messages import HumanMessage, SystemMessage
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image, ImageStat
from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator

from master.agents import BaseAgent
from master.agents.common.tools import ToolsRegistry
from master.agents.common.message import Intent, MessageRequest
from master.agents.common.state import AgentState
from master.agents.common.llm_client import LLMClient
from master.agents.common.prompt import (
    parser_document_review_instruction,
    parser_ocr_instruction,
    parser_page_review_instruction,
    parser_review_system_prompt,
    parser_system_prompt,
)

import asyncio
import base64
import datetime
import uuid
import json
import fitz
import io
import re
import os
import unicodedata


# OCR config
MIN_GRAYSCALE_RANGE = 10
WHITE_PIXEL_THRESHOLD = 247
MIN_NON_WHITE_RATIO = 0.003

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}

load_dotenv(override=True)

class Type(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_ans"

class QuestionOutput(BaseModel):
    question_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question_index: int = Field(description="Số thứ tự câu hỏi trong đề, bắt đầu từ 1")
    type: Type = Field(description="Loại câu hỏi, là 1 trong 3 loại sau 'multiple_choice' hoặc 'true_false' hoặc 'short_ans'")
    content: str = Field(description="Nội dung câu hỏi, có thể bao gồm cả text và LaTeX, bỏ phần đầu như 'Câu 1: ' hoặc '1.'")
    options: Optional[list[str]] = Field(default=None, description="Danh sách lựa chọn nếu là câu hỏi trắc nghiệm, để trống nếu là câu hỏi tự luận")
    has_image: bool = Field(description="Câu hỏi có chứa hình ảnh hay không")
    image_url: Optional[str] = Field(default=None, description="URL của hình ảnh nếu có")
    generated: bool = Field(default=False, description="True nếu câu hỏi được tạo ra bởi LLM, False nếu được trích xuất trực tiếp từ đề thi. Nếu generated = True thì các trường có thể không chính xác và chỉ mang tính tham khảo.")


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
    

class OCRQuestionReviewOutput(BaseModel):
    question_marker: Optional[str] = None
    type: Type
    content: str
    options: list[str] = Field(default_factory=list)
    has_image: bool = False
    image_url: Optional[str] = None


class OCRPageReviewOutput(BaseModel):
    metadata: OCRMetadataOutput = Field(default_factory=OCRMetadataOutput)
    questions: list[OCRQuestionReviewOutput] = Field(default_factory=list)


class ParserAgent(ToolsRegistry, BaseAgent):

    def __init__(self):
        super().__init__(agent_role="Parser")
        self.system_prompt = parser_system_prompt()
        self._llm = None
        self._review_llm = None
        self._review_llm_with_output = None
        self._review_system_prompt = parser_review_system_prompt()

    async def setup(self):
        self.logger.agent_node("Parser setup started")
        llm = LLMClient.chat_model(
            provider="openai_compatible",
            base_url=os.getenv("FPT_BASE_URL"),
            api_key=os.getenv("FPT_API_KEY"),
            model=os.getenv("PARSER_MODEL"),
            temperature=0.1,
            top_p=0.8,
            max_tokens=8192,
        )
        self._llm = llm
        review_provider = os.getenv("PARSER_REVIEW_PROVIDER") or "openai_compatible"
        review_base_url = os.getenv("PARSER_REVIEW_BASE_URL") or os.getenv("FPT_BASE_URL")
        review_api_key = os.getenv("PARSER_REVIEW_API_KEY") or os.getenv("FPT_API_KEY")
        review_model = os.getenv("PARSER_REVIEW_MODEL")

        try:
            self._review_llm = LLMClient.chat_model(
                provider=review_provider,
                base_url=review_base_url,
                api_key=review_api_key,
                model=review_model,
                temperature=0.0,
                top_p=0.7,
                max_tokens=4096,
            )
            self._review_llm_with_output = self._review_llm.with_structured_output(
                OCRPageReviewOutput
            )
        except Exception as error:
            self.logger.warning(f"Parser review LLM setup failed, fallback to OCR LLM: {error}")
            self._review_llm = self._llm
            self._review_llm_with_output = self._review_llm.with_structured_output(
                OCRPageReviewOutput
            )
        self.logger.agent_node("Parser setup completed")

    def _extract_options_from_content(self, content: str, options: list | None) -> tuple[str, list[str]]:
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

        first_option_start = matches[0].start()
        cleaned_content = content[:first_option_start].strip()

        self.logger.agent_node(f"Parser extracted {len(extracted_options)} options from content for true_false question")
        return cleaned_content, extracted_options

    def _normalize_question_type(self, raw_type: str | None, options: list | None) -> Type:
        if options and len(options) >= 2:
            has_uppercase = all(isinstance(opt, str) and re.match(r'^[A-D]\.', opt.strip()) for opt in options)
            has_lowercase = all(isinstance(opt, str) and re.match(r'^[a-d][.)]', opt.strip()) for opt in options)
            if has_uppercase and len(options) == 4:
                return Type.MULTIPLE_CHOICE
            if has_lowercase:
                return Type.TRUE_FALSE

        if raw_type:
            raw = str(raw_type).strip().lower()
            
            if raw in {"short_ans", "short_answer", "tự luận", "tu luan"}:
                return Type.SHORT_ANSWER
                
            if raw in {"multiple_choice", "multiple choice", "trắc nghiệm", "trac nghiem"}:
                return Type.MULTIPLE_CHOICE
                
            if raw in {"true_false", "true false", "đúng sai", "đúng/sai", "dung sai"}:
                return Type.TRUE_FALSE if options else Type.SHORT_ANSWER
                
            try:
                return Type(raw)
            except ValueError:
                pass

        if not options:
            return Type.SHORT_ANSWER

        return Type.MULTIPLE_CHOICE
    def _decode_escaped_text(self, text: str | None) -> str:
        normalized = str(text or "").strip()
        if not normalized:
            return ""

        if any(token in normalized for token in ('\\"', "\\n", "\\r", "\\t")):
            normalized = (
                normalized
                .replace("\\r", "\r")
                .replace("\\n", "\n")
                .replace("\\t", "\t")
                .replace('\\"', '"')
            )

        return normalized.strip()

    def _fold_text(self, text: str | None) -> str:
        normalized = unicodedata.normalize("NFD", str(text or ""))
        without_marks = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
        return without_marks.replace("đ", "d").replace("Đ", "D").lower()

    def _starts_with_question_marker(self, text: str | None) -> bool:
        return bool(re.match(r"^\s*(?:cau|bai)\s*\d+\b", self._fold_text(text), flags=re.IGNORECASE))

    def _extract_embedded_questions(self, text: str | None) -> list[dict]:
        normalized = self._decode_escaped_text(text)
        if not normalized:
            return []

        candidates: list[str] = []

        def add_candidate(value: str) -> None:
            candidate = value.strip()
            if candidate and candidate not in candidates:
                candidates.append(candidate)

        add_candidate(normalized)

        start = normalized.find("{")
        end = normalized.rfind("}")
        if 0 <= start < end:
            add_candidate(normalized[start:end + 1])

        trimmed = normalized.lstrip().strip(",")
        if not trimmed.startswith("{") and ('"metadata"' in trimmed or '"questions"' in trimmed):
            add_candidate("{" + trimmed + "}")

        for candidate in candidates:
            try:
                payload = json.loads(candidate)
            except json.JSONDecodeError:
                continue

            if isinstance(payload, str):
                try:
                    payload = json.loads(payload)
                except json.JSONDecodeError:
                    continue

            if isinstance(payload, dict) and isinstance(payload.get("questions"), list):
                embedded_questions = [question for question in payload["questions"] if isinstance(question, dict)]
                if embedded_questions:
                    return embedded_questions

        return []

    def _normalize_question_content(self, content: str | None) -> str:
        normalized = self._decode_escaped_text(content)
        if not normalized:
            return ""

        section_heading_pattern = re.compile(
            r"^\s*(?:Phần|Phan)\s+(?:[IVXLCDM]+|\d+)\s*[\.:¼：\-–—]?\s*"
            r".*?(?=(?:Câu|Cau|Bài|Bai)\s*\d+\b|$)",
            flags=re.IGNORECASE | re.DOTALL,
        )
        normalized = section_heading_pattern.sub("", normalized).strip()

        normalized = re.sub(
            r"^\s*(?:Thí sinh|Thi sinh)\s+trả lời.*?(?=(?:Câu|Cau|Bài|Bai)\s*\d+\b|$)",
            "",
            normalized,
            flags=re.IGNORECASE | re.DOTALL,
        ).strip()

        if '"metadata"' in normalized[:300] or '"questions"' in normalized[:300]:
            question_start = re.search(
                r"\b(Câu|Cau|Bài|Bai)\s*\d+\b",
                normalized,
                flags=re.IGNORECASE,
            )
            if question_start:
                normalized = normalized[question_start.start():]
            elif re.search(r'^\s*[{[]?\s*"?(metadata|questions)"?\s*:', normalized, flags=re.IGNORECASE):
                return ""

        normalized = re.sub(r"^(?:Câu|Cau|Bài|Bai)\s*\d+\s*[:.\-]?\s*", "", normalized, flags=re.IGNORECASE).strip()

        return normalized
    def _normalize_options(self, options: list | None) -> list[str]:
        if not isinstance(options, list):
            return []

        normalized_options: list[str] = []
        for option in options:
            normalized = self._decode_escaped_text(str(option))
            if normalized:
                normalized_options.append(normalized)

        return normalized_options

    def _extract_multiple_choice_options_from_content(self, content: str, options: list | None) -> tuple[str, list[str]]:
        if options and len(options) == 4:
            return content, options

        marker_pattern = re.compile(r"(?<!\w)([A-D][\.\)])\s*", re.IGNORECASE)
        matches = list(marker_pattern.finditer(content))
        if len(matches) < 4:
            return content, options or []

        for start_idx in range(0, len(matches) - 3):
            selected = matches[start_idx:start_idx + 4]
            labels = [match.group(1)[0].upper() for match in selected]
            if labels != ["A", "B", "C", "D"]:
                continue

            extracted_options: list[str] = []
            for idx, match in enumerate(selected):
                start = match.start()
                end = selected[idx + 1].start() if idx + 1 < len(selected) else len(content)
                option_block = content[start:end].strip()
                option_text = re.sub(r"^[A-Da-d][\.\)]\s*", "", option_block).strip()
                extracted_options.append(f"{labels[idx]}. {option_text}")

            cleaned_content = content[:selected[0].start()].strip()
            self.logger.agent_node(f"Parser extracted {len(extracted_options)} options from content for multiple_choice question")
            return cleaned_content, extracted_options

        return content, options or []

    def _extract_questions_from_ocr_payload(self, payload: dict) -> list[dict]:
        page_questions: list[dict] = []

        if isinstance(payload, dict) and isinstance(payload.get("questions"), list):
            page_questions = [q for q in payload["questions"] if isinstance(q, dict)]
        elif isinstance(payload, dict) and "content" in payload:
            page_questions = [payload]
        elif isinstance(payload, dict) and "raw_text" in payload:
            page_questions = [{"content": payload.get("raw_text", "")}]

        normalized_page_questions: list[dict] = []
        for item in page_questions:
            embedded_questions = self._extract_embedded_questions(item.get("content"))
            if embedded_questions:
                normalized_page_questions.extend(embedded_questions)
                self.logger.agent_node(f"Parser expanded embedded OCR JSON into {len(embedded_questions)} questions")
                continue
            normalized_page_questions.append(item)

        return normalized_page_questions

    def _has_question_marker(self, item: dict) -> bool:
        marker = str(item.get("question_marker") or "").strip()
        if marker:
            return self._starts_with_question_marker(marker)

        return self._starts_with_question_marker(item.get("content"))

    def _merge_continuation_questions(self, questions: list[dict]) -> list[dict]:
        merged: list[dict] = []

        for item in questions:
            if not isinstance(item, dict):
                continue

            if self._has_question_marker(item) or not merged:
                merged.append(dict(item))
                continue

            previous = merged[-1]
            continuation_content = self._normalize_question_content(item.get("content"))
            if continuation_content:
                previous_content = str(previous.get("content") or "").strip()
                previous["content"] = (
                    f"{previous_content}\n{continuation_content}".strip()
                    if previous_content
                    else continuation_content
                )

            previous_options = self._normalize_options(previous.get("options"))
            continuation_options = self._normalize_options(item.get("options"))
            if continuation_options:
                seen_labels = {option.strip()[:2].upper() for option in previous_options if isinstance(option, str) and option.strip()}
                for option in continuation_options:
                    label = option.strip()[:2].upper()
                    if label not in seen_labels:
                        previous_options.append(option)
                        seen_labels.add(label)
                previous["options"] = previous_options

            previous["has_image"] = bool(previous.get("has_image")) or bool(item.get("has_image"))
            if not previous.get("image_url") and item.get("image_url"):
                previous["image_url"] = item.get("image_url")

        return merged


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

    def _drop_white_page(self, image_bytes: bytes) -> bool:
        try:
            with Image.open(io.BytesIO(image_bytes)) as image:
                grayscale = image.convert("L")
                stats = ImageStat.Stat(grayscale)
                min_pixel, max_pixel = stats.extrema[0]

                if max_pixel - min_pixel < MIN_GRAYSCALE_RANGE and stats.mean[0] >= WHITE_PIXEL_THRESHOLD:
                    return False

                histogram = grayscale.histogram()
                total_pixels = max(1, sum(histogram))
                non_white_pixels = sum(histogram[:WHITE_PIXEL_THRESHOLD])
                return (non_white_pixels / total_pixels) >= MIN_NON_WHITE_RATIO
        except Exception as error:
            self.logger.error(f"Drop white page failed: {error}")
            return False

    def _invoke_ocr(self, image_bytes: bytes, instruction: str) -> dict:
        if self._llm is None:
            raise RuntimeError("Parser OCR model is not initialized. Call setup() before OCR.")

        message = HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": instruction
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
            raw = "".join(chunk.get("text", "") if isinstance(chunk, dict) else str(chunk) for chunk in content)
        else:
            raw = str(content)

        clean = raw.strip()
        clean = re.sub(r"^```json\s*", "", clean)
        clean = re.sub(r"\s*```$", "", clean)

        try:
            return json.loads(clean)
        except json.JSONDecodeError:
            return {"raw_text": clean}

    def _count_questions_in_payload(self, payload: dict) -> int:
        return len(self._extract_questions_from_ocr_payload(payload))

    def _page_ocr_text(self, payload: dict) -> str:
        if not isinstance(payload, dict):
            return ""

        parts: list[str] = []
        for question in self._extract_questions_from_ocr_payload(payload):
            marker = str(question.get("question_marker") or "").strip()
            content = self._decode_escaped_text(question.get("content"))
            options = self._normalize_options(question.get("options"))
            section = "\n".join(part for part in [marker, content, *options] if part)
            if section:
                parts.append(section)

        raw_text = self._decode_escaped_text(payload.get("raw_text"))
        if raw_text:
            parts.append(raw_text)

        return "\n\n".join(parts).strip()

    def _review_page_ocr_output(self, *, page_num: int, image_bytes: bytes, ocr_output: dict, previous_page_context: str = "") -> dict:
        if not getattr(self, "_review_llm_with_output", None):
            return ocr_output

        instruction = parser_page_review_instruction(
            page_num=page_num,
            current_page_candidate_json=json.dumps(ocr_output, ensure_ascii=False, indent=2),
            previous_page_context=previous_page_context,
        )
        message = HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": instruction,
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{base64.b64encode(image_bytes).decode('utf-8')}"
                    },
                },
            ]
        )

        raw_count = self._count_questions_in_payload(ocr_output)
        try:
            review_result: OCRPageReviewOutput = self._review_llm_with_output.invoke(
                [
                    SystemMessage(content=self._review_system_prompt),
                    message,
                ]
            )
        except Exception as error:
            self.logger.warning(f"Parser page review failed page={page_num}: {error}")
            return ocr_output

        reviewed_payload = review_result.model_dump(exclude_none=True)
        reviewed_count = self._count_questions_in_payload(reviewed_payload)

        self.logger.agent_node(f"Parser page review applied page={page_num} questions_before={raw_count} questions_after={reviewed_count}")
        return reviewed_payload

    def _ocr_single_page(self, page_num: int, image_bytes: bytes) -> dict:
        return self._invoke_ocr(image_bytes, parser_ocr_instruction())

    def _flatten_page_questions(self, ocr_pages: list[tuple[int, dict]]) -> dict:
        return {
            "metadata": ocr_pages[0][1].get("metadata", {}) if ocr_pages else {},
            "questions": [question for _, page in ocr_pages for question in self._extract_questions_from_ocr_payload(page)],
        }

    def _review_document_ocr_output(self, *, page_payloads: list[tuple[int, bytes, str]], ocr_pages: list[tuple[int, dict]],) -> dict:
        if not getattr(self, "_review_llm_with_output", None):
            return self._flatten_page_questions(ocr_pages)

        page_nums = {page_num for page_num, _ in ocr_pages}
        current_document_candidate = {
            "pages": [
                {
                    "page_num": page_num,
                    "ocr_output": page,
                }
                for page_num, page in ocr_pages
            ]
        }
        message_content = [
            {
                "type": "text",
                "text": parser_document_review_instruction(
                    json.dumps(current_document_candidate, ensure_ascii=False, indent=2)
                ),
            }
        ]
        for page_num, image_bytes, _ in sorted(page_payloads, key=lambda item: item[0]):
            if page_num not in page_nums:
                continue
            message_content.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{base64.b64encode(image_bytes).decode('utf-8')}"
                    },
                }
            )

        raw_count = sum(self._count_questions_in_payload(page) for _, page in ocr_pages)
        try:
            review_result: OCRPageReviewOutput = self._review_llm_with_output.invoke(
                [
                    SystemMessage(content=self._review_system_prompt),
                    HumanMessage(content=message_content),
                ]
            )
        except Exception as error:
            self.logger.warning(f"Parser document review failed: {error}")
            return self._flatten_page_questions(ocr_pages)

        reviewed_payload = review_result.model_dump(exclude_none=True)
        reviewed_count = self._count_questions_in_payload(reviewed_payload)
        self.logger.agent_node(f"Parser document review applied questions_before={raw_count} questions_after={reviewed_count}")
        return reviewed_payload

    async def _ocr_file(self, file_path: str, batch_size: Optional[int] = None) -> list[dict]:
        if not os.path.exists(file_path):
            self.logger.warning(f"Parser input file not found: {file_path}")
            return {"metadata": {}, "questions": []}

        extension = os.path.splitext(file_path)[1].lower()
        if extension not in ALLOWED_EXTENSIONS:
            self.logger.warning(f"Parser input extension not supported: {extension}")
            return {"metadata": {}, "questions": []}

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

            self.logger.agent_node(f"Parser OCR batch {batch_index}/{total_batches} started pages={batch_page_nums}")

            with ThreadPoolExecutor(max_workers=batch_size) as executor:
                future_map = {
                    executor.submit(self._ocr_single_page, page_num, image_bytes): page_num
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
        ocr_pages = [(page_num, all_results[page_num]) for page_num in sorted(all_results.keys())]
        page_payload_map = {page_num: image_bytes for page_num, image_bytes, _ in page_payloads}
        reviewed_pages: list[tuple[int, dict]] = []
        previous_page_context = ""

        for page_num, ocr_output in ocr_pages:
            image_bytes = page_payload_map.get(page_num)
            if image_bytes is None:
                continue

            reviewed_output = self._review_page_ocr_output(
                page_num=page_num,
                image_bytes=image_bytes,
                ocr_output=ocr_output,
                previous_page_context=previous_page_context,
            )
            reviewed_pages.append((page_num, reviewed_output))
            previous_page_context = self._page_ocr_text(reviewed_output) or self._page_ocr_text(ocr_output)

        ocr_pages = reviewed_pages
        document_output = self._review_document_ocr_output(page_payloads=page_payloads, ocr_pages=ocr_pages)

        questions: list[QuestionOutput] = []
        question_index = 0
        dropped_count = 0

        document_questions = self._merge_continuation_questions(self._extract_questions_from_ocr_payload(document_output))

        for item in document_questions:
            page_num = item.get("page_num", 0)
            # Get question content and normalize it to remove leaked JSON scaffolding
            content = self._normalize_question_content(item.get("content"))
            if not content:
                continue

            question_index += 1

            # Check if question has image and get image URL if available
            image_url = item.get("image_url")
            has_image = bool(item.get("has_image"))
            if not has_image:
                lower_content = content.lower()
                has_image = bool(image_url) or "![" in content or "<img" in lower_content
            
            # Extract options if it's a multiple choice question
            options = self._normalize_options(item.get("options"))
            
            # Normalize: extract options embedded in content for true_false questions
            raw_type = item.get("type", "")
            raw_type_lower = str(raw_type).strip().lower() if raw_type else ""
            if raw_type_lower in {"true_false", "true false", "Ã„â€˜ÃƒÂºng sai", "Ã„â€˜ÃƒÂºng/sai", "dung sai"} or not options:
                content, options = self._extract_options_from_content(content, options)

            # Get the type of the question
            question_type = self._normalize_question_type(item.get("type"), options)

            if question_type == Type.MULTIPLE_CHOICE and len(options) != 4:
                content, options = self._extract_multiple_choice_options_from_content(content, options)
                question_type = self._normalize_question_type(item.get("type"), options)

            if question_type == Type.TRUE_FALSE and not options:
                self.logger.warning(f"Parser downgraded question index={question_index} from true_false to short_ans because options are missing")
                question_type = Type.SHORT_ANSWER

            if question_type == Type.MULTIPLE_CHOICE and len(options) != 4:
                self.logger.warning(f"Parser downgraded question index={question_index} page={page_num} from multiple_choice to short_ans because options are still incomplete")
                question_type = Type.SHORT_ANSWER
                options = []

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
                dropped_count += 1
                self.logger.warning(
                    f"Parser question DROPPED index={question_index} "
                    f"type={question_type} raw_type={raw_type} "
                    f"error={error}"
                )
                continue

            # Add question object to the list
            questions.append(question_obj)

        self.logger.agent_node(f"Parser extraction complete: kept={len(questions)} dropped={dropped_count} total_seen={question_index}")

        return {
            "metadata": document_output.get("metadata", {}),
            "questions": [q.model_dump() for q in questions],
        }
    
    async def parser(self, state: AgentState) -> AgentState:
        request = state["request"]
        file_path = request.file_path
        if not file_path:
            self.logger.warning("Parser request missing file_path in parser_output")
            
            return AgentState(request=request)

        ocr_result = await self._ocr_file(file_path, batch_size=2)
        questions_data = ocr_result.get("questions", [])
        metadata = ocr_result.get("metadata", {})
        
        self.logger.agent_node(f"Parser extracted {len(questions_data)} questions from file")
        
        exam_id = request.exam_id or str(uuid.uuid4())
        
        # Link questions to exam_id
        for q in questions_data:
            q["exam_id"] = exam_id
            
        # Create exam record
        exam = {
            "id": exam_id,
            "subject": metadata.get("subject"),
            "exam_type": metadata.get("exam_type"),
            "year": metadata.get("year"),
            "grade": metadata.get("grade"),
            "source": metadata.get("source"),
            "total_questions": len(questions_data),
            "duration": metadata.get("duration"),
            "created_at": datetime.datetime.now().isoformat(),
            "questions": [q.get("question_id") for q in questions_data],
            "generated": False,
        }

        await self.insert_data("masterthpt", "exams", [exam])
        self.logger.agent_node(f"Parser saved exam {exam_id} with {len(questions_data)} questions to database")

        request = MessageRequest(
            intent=request.intent,
            student_id=request.student_id,
            exam_id=exam_id,
            question_id=request.question_id,
            parser_output=questions_data,
        )

        return AgentState(request=request)
    
    def parser_router(self, state: AgentState) -> str:
        request = state["request"]
        if request.intent == Intent.PREPROCESS.value:
            return "parser"
        return "teacher"


    async def run(self, input: str) -> str:
        pass

if __name__ == "__main__":
    parser_agent = ParserAgent()
    asyncio.run(parser_agent.setup())
#     # file_path="c:\\Users\\abcsd\\Downloads\\Đề cuối kỳ 2 Toán 10 năm 2024 - 2025 trường THPT Lê Hồng Phong - Đắk Lắk - TOANMATH.com.pdf"
#     # file_path="c:\\Users\\abcsd\\Downloads\\Đề cuối kỳ 2 Toán 11 năm 2024 - 2025 trường THPT Lê Hồng Phong - Đắk Lắk - TOANMATH.com.pdf"
    file_path="c:\\Users\\abcsd\\Downloads\\Đề cuối kỳ 2 Toán 12 năm 2024 - 2025 trường THPT Lê Hồng Phong - Đắk Lắk - TOANMATH.com.pdf"
    asyncio.run(parser_agent._ocr_file(file_path, batch_size=2))
