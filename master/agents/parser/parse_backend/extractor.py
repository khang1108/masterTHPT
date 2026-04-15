import base64
import io
import json
import mimetypes
import os
import re
import time
import unicodedata
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from google import genai
from PIL import Image
from pydantic import BaseModel, Field

from config import config


def _load_valid_tags() -> list[str]:
    """Load the allowed topic tags from the local knowledge base."""
    kb_path = os.path.join(os.path.dirname(__file__), "math_knowledge_base.json")

    try:
        with open(kb_path, "r", encoding="utf-8") as file:
            kb_data = json.load(file)
    except Exception as error:
        print(f"[Extractor] Failed to load knowledge base: {error}")
        return ["unknown"]

    valid_tags: list[str] = []
    for node in kb_data.get("nodes", []):
        node_id = node.get("id")
        if node_id and node_id not in valid_tags:
            valid_tags.append(node_id)

        for prerequisite in node.get("prerequisites", []):
            if prerequisite not in valid_tags:
                valid_tags.append(prerequisite)

    return valid_tags or ["unknown"]


VALID_TAGS = _load_valid_tags()
TopicTagEnum = Enum("TopicTagEnum", {tag.replace(".", "_"): tag for tag in VALID_TAGS})


class QuestionNode(BaseModel):
    id: str = Field(description="Unique ID (sẽ bị ghi đè bởi hash UUID).")
    question_index: int = Field(description="Số thứ tự câu hỏi (1-based)")
    type: Literal["multiple_choice", "short_ans", "true_false"] = Field(description="Loại câu hỏi")
    content: str = Field(description="Nội dung câu hỏi dạng plain text")
    options: Optional[List[str]] = Field(None, description="Đáp án CHỈ cho multiple_choice")
    correct_answer: Optional[str] = Field(None, description="Đáp án đúng nếu xác định được")
    has_image: bool = Field(default=False, description="True nếu có visual asset gắn với câu")
    image_url: Optional[str] = Field(None, description="Đường dẫn ảnh nếu có")
    difficulty_a: Optional[float] = Field(None, description="IRT discrimination — NULL, tính sau")
    difficulty_b: Optional[float] = Field(None, description="IRT difficulty — NULL, tính sau")
    topic_tags: List[TopicTagEnum] = Field(description="BẮT BUỘC chọn từ Knowledge Base Enum")


class ExamDocument(BaseModel):
    id: str = Field(description="UUID định danh đề thi")
    file_type: Literal["image", "pdf"] = Field(description="Nguồn đầu vào")
    subject: str = Field(description="Môn học (VD: Toán, Vật lý, Hóa học)")
    grade: Optional[int] = Field(None, description="Khối lớp (10, 11, 12)")
    exam_type: str = Field(description="Loại kỳ thi đầy đủ tiếng Việt có dấu")
    year: Optional[int] = Field(None, description="Năm thi")
    source: Optional[str] = Field(None, description="Nguồn xuất xứ đầy đủ tiếng Việt có dấu")
    total_questions: int = Field(description="Tổng số câu hỏi")
    generated: bool = Field(default=False, description="Định nghĩa đề thi được gen ra")
    duration: Optional[int] = Field(None, description="Thời gian làm bài (phút)")
    metadata: Optional[str] = Field(None, description="Metadata bổ sung")
    created_at: Optional[str] = Field(None, description="Timestamp tạo bản ghi")
    questions: List[QuestionNode]


MAX_CHARS_PER_BATCH = 150_000
RATE_LIMIT_SLEEP_SECONDS = 12
GEMINI_RETRY_COUNT = 3
GEMINI_RETRY_DELAY_SECONDS = 7


class OutputStructuring:

    def __init__(self):
        if not config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is missing.")

        self.client = genai.Client(api_key=config.GEMINI_API_KEY)


    @staticmethod
    def _image_to_data_url(path: str) -> Optional[str]:
        try:
            mime_type = mimetypes.guess_type(path)[0] or "image/png"
            with open(path, "rb") as file:
                encoded = base64.b64encode(file.read()).decode("utf-8")
            return f"data:{mime_type};base64,{encoded}"
        except Exception as error:
            print(f"[Extractor] Image encode failed: {error}")
            return None


    def _build_prompt(
        self,
        questions_list: List[Dict],
        source_type: str = "pdf",
        batch_info: str = "",
    ) -> List[Dict[str, Any]]:
        """Build the multimodal prompt payload."""
        grouped_content = ""
        expected_question_count = len(questions_list)

        for index, question in enumerate(questions_list, start=1):
            grouped_content += (
                f"\n--- [BLOCK CÂU HỎI {index} : ID = {question.get('question_id', '')}] ---\n"
                f"{question.get('raw_text', '')}\n"
            )

        valid_tags_str = "\n".join(f"  - {tag}" for tag in VALID_TAGS)
        text_prompt = f"""Bạn là chuyên gia phân tích đề thi giáo dục Việt Nam. Trích xuất câu hỏi thành JSON chuẩn.

{batch_info}
File: {source_type}
SỐ CÂU OCR ĐÃ GOM ĐƯỢC: {expected_question_count}

=== TOPIC TAGS HỢP LỆ (BẮT BUỘC chọn từ đây, CẤM bịa tag mới) ===
{valid_tags_str}

=== DỮ LIỆU ĐẦU VÀO ===
{grouped_content}

=== QUY TẮC ƯU TIÊN CAO ===
1. Phải xuất đúng đủ {expected_question_count} câu hỏi nếu dữ liệu OCR đầu vào có đủ {expected_question_count} block câu hỏi.
2. Khi đã xuất đủ {expected_question_count} câu thì DỪNG NGAY, bỏ toàn bộ phần nội dung phía dưới nếu còn.
3. KHÔNG được tự ý cắt xuống ít hơn {expected_question_count} câu trừ khi dữ liệu đầu vào thực sự không đủ câu.
4. Nếu thấy phần dư, phần lặp, hoặc mã đề khác sau khi đã đủ {expected_question_count} câu thì bỏ qua toàn bộ.
5. `total_questions` trong JSON phải khớp đúng với số câu thực sự xuất ra.

=== QUY TẮC CHUNG ===
1. Output tiếng Việt phải có dấu đầy đủ.
2. Sửa lỗi OCR trong `content`, `options`, 
4. Nếu một câu có các ý `a)`, `b)`, `c)`, `d)` theo kiểu nhận định đúng/sai thì PHẢI gom toàn bộ vào cùng một câu hỏi, không tách thành nhiều câu riêng.
5. Với dạng đúng/sai nhiều ý, dùng `type = "true_false"`.
6. Với dạng đúng/sai nhiều ý, format `content` đẹp theo nhiều dòng:
   - dòng đầu là thân câu hỏi chung
   - mỗi ý `a)`, `b)`, `c)`, `d)` trên một dòng riêng
7. Ưu tiên suy luận nhanh `correct_answer` nếu đủ dữ kiện; nếu không chắc thì để `null`.

=== SCHEMA CÂU HỎI (QuestionNode) ===
- `id`: giá trị bất kỳ (hệ thống ghi đè)
- `question_index`: số thứ tự 1-based ("Câu 19" → 19)
- `type`: "multiple_choice" | "short_ans" | "true_false"
- `content`: nội dung đã sửa lỗi, tiếng Việt có dấu. Nếu có các ý `a,b,c,d` thì giữ chung trong một câu và xuống dòng cho dễ đọc
- `options`: chỉ cho multiple_choice, null cho loại khác
- `correct_answer`: đáp án đúng hoặc đáp án dự đoán nhanh nếu suy ra được, nếu không chắc thì null
- `has_image`, `image_url`: hệ thống sẽ đồng bộ lại từ OCR. Nếu không chắc thì có thể để false/null.
- `topic_tags`: BẮT BUỘC chọn từ Knowledge Base

Chỉ lấy đến khi đủ {expected_question_count} câu hỏi, sau đó dừng và bỏ phần còn lại.

=== SCHEMA ĐỀ THI (ExamDocument) ===
- `subject`: tên môn tiếng Việt có dấu ("Toán", "Vật lý", "Hóa học")
- `grade`: khối lớp (10, 11, 12) hoặc null
- `exam_type`: viết đầy đủ tiếng Việt có dấu ("Kiểm tra giữa kỳ 1", "Thi tốt nghiệp THPT Quốc gia")
- `source`: tên trường/sở đầy đủ dấu ("Sở GDĐT Hà Nội", "Trường THPT chuyên Lê Hồng Phong")
- `year`, `duration`, `total_questions`: trích xuất hoặc null

Trường `id` sẽ bị GHI ĐÈ tự động."""

        prompt_parts: List[Dict[str, Any]] = [{"type": "text", "text": text_prompt}]

        for index, question in enumerate(questions_list, start=1):
            abs_path = question.get("image_path")
            if not abs_path:
                continue

            data_url = self._image_to_data_url(abs_path)
            if not data_url:
                continue

            prompt_parts.append({"type": "text", "text": f"Ảnh minh họa cho BLOCK CÂU HỎI {index}"})
            prompt_parts.append({"type": "image_url", "image_url": {"url": data_url}})

        return prompt_parts


    @staticmethod
    def _prompt_parts_to_gemini_contents(prompt_parts: List[Dict[str, Any]]) -> List[Any]:
        contents: List[Any] = []

        for part in prompt_parts:
            part_type = part.get("type")

            if part_type == "text":
                text = part.get("text")
                if text:
                    contents.append(text)
                continue

            if part_type != "image_url":
                continue

            url = part.get("image_url", {}).get("url")
            if not url or not url.startswith("data:"):
                continue

            try:
                _, encoded = url.split(",", 1)
                image_bytes = base64.b64decode(encoded)
                image = Image.open(io.BytesIO(image_bytes))
                image.load()
                contents.append(image)
            except Exception as error:
                print(f"[Extractor] Image decode failed: {error}")

        return contents


    @staticmethod
    def _generate_exam_id(questions_list: List[Dict]) -> str:
        total_raw = "".join(question.get("raw_text", "") for question in questions_list)
        return str(uuid.uuid5(uuid.NAMESPACE_OID, total_raw))


    @staticmethod
    def _generate_question_id(exam_id: str, question_index: int) -> str:
        return str(uuid.uuid5(uuid.NAMESPACE_OID, f"{exam_id}_{question_index}"))


    @staticmethod
    def _extract_source_question_index(question_data: Dict[str, Any]) -> Optional[int]:
        hint = question_data.get("question_index_hint")
        if isinstance(hint, int):
            return hint

        raw_text = question_data.get("raw_text", "")
        normalized_text = unicodedata.normalize("NFD", raw_text or "")
        normalized_text = "".join(
            char for char in normalized_text if unicodedata.category(char) != "Mn"
        )
        normalized_text = normalized_text.replace("đ", "d").replace("Đ", "D").lower()

        for line in normalized_text.splitlines():
            match = re.search(r"^\s*(?:\[[^\]]+\]\s*)?(cau|bai)\s*(\d+)\b", line)
            if not match:
                continue

            try:
                return int(match.group(2))
            except (TypeError, ValueError):
                return None

        return None


    def _assign_hash_ids(self, document: ExamDocument, exam_id: str) -> ExamDocument:
        """Override model ids with stable local ids."""
        document.id = exam_id
        document.created_at = datetime.now(timezone.utc).isoformat()

        for question in document.questions:
            question.id = self._generate_question_id(exam_id, question.question_index)

        document.total_questions = len(document.questions)
        return document


    def _merge_ocr_image_info(
        self,
        document: ExamDocument,
        questions_list: List[Dict],
    ) -> ExamDocument:
        """Fill image fields from OCR metadata."""
        image_url_by_index: Dict[int, str] = {}
        fallback_urls_by_position: List[Optional[str]] = []
        has_indexed_images = False

        for source_question in questions_list:
            image_url = source_question.get("image_url")
            fallback_urls_by_position.append(image_url)

            source_index = self._extract_source_question_index(source_question)
            if source_index is None or not image_url:
                continue

            image_url_by_index[source_index] = image_url
            has_indexed_images = True

        used_image_urls: set[str] = set()

        for index, question in enumerate(document.questions):
            matched_url = image_url_by_index.get(question.question_index)
            if (
                not matched_url
                and not has_indexed_images
                and index < len(fallback_urls_by_position)
            ):
                matched_url = fallback_urls_by_position[index]

            if matched_url in used_image_urls:
                matched_url = None

            question.image_url = matched_url
            question.has_image = bool(matched_url)
            if matched_url:
                used_image_urls.add(matched_url)

        return document


    def structure_output(
        self,
        questions_list: List[Dict],
        source_type: str = "pdf",
    ) -> ExamDocument:
        exam_id = self._generate_exam_id(questions_list)
        total_chars = sum(len(question.get("raw_text", "")) for question in questions_list)

        print(f"[Extractor] Build document for {len(questions_list)} blocks")

        if total_chars <= MAX_CHARS_PER_BATCH:
            document = self._call_model(questions_list, source_type)
        else:
            document = self._process_multi_batch(questions_list, source_type)

        document = self._merge_ocr_image_info(document, questions_list)
        document = self._assign_hash_ids(document, exam_id)
        print(f"[Extractor] Ready exam={document.id} questions={document.total_questions}")
        return document


    def _call_model(
        self,
        questions_list: List[Dict],
        source_type: str,
        batch_info: str = "",
    ) -> ExamDocument:
        prompt_parts = self._build_prompt(questions_list, source_type, batch_info)
        contents = self._prompt_parts_to_gemini_contents(prompt_parts)
        last_error = None

        for attempt in range(1, GEMINI_RETRY_COUNT + 1):
            try:
                response = self.client.models.generate_content(
                    model=config.GEMINI_MODEL,
                    contents=contents,
                    config=genai.types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=ExamDocument,
                        temperature=config.LLM_TEMPERATURE,
                    ),
                )

                if getattr(response, "parsed", None) is not None:
                    parsed = response.parsed
                    if isinstance(parsed, ExamDocument):
                        return parsed
                    return ExamDocument.model_validate(parsed)

                return ExamDocument.model_validate_json(response.text)
            except Exception as error:
                last_error = error
                print(f"[Extractor] Gemini attempt {attempt}/{GEMINI_RETRY_COUNT} failed: {error}")
                if attempt < GEMINI_RETRY_COUNT:
                    time.sleep(GEMINI_RETRY_DELAY_SECONDS)

        raise RuntimeError(
            f"Gemini request failed after {GEMINI_RETRY_COUNT} attempts: {last_error}"
        )


    def _process_multi_batch(
        self,
        questions_list: List[Dict],
        source_type: str,
    ) -> ExamDocument:
        chunks = self._split_into_chunks(questions_list)
        total_batches = len(chunks)
        all_questions: List[QuestionNode] = []
        first_result: ExamDocument | None = None

        print(f"[Extractor] Split into {total_batches} batches")

        for index, chunk in enumerate(chunks, start=1):
            batch_info = f"Batch {index}/{total_batches}"
            print(f"[Extractor] Run {batch_info} size={len(chunk)}")

            if index > 1:
                time.sleep(RATE_LIMIT_SLEEP_SECONDS)

            result = self._call_model(chunk, source_type, batch_info)
            if first_result is None:
                first_result = result

            all_questions.extend(result.questions)

        return ExamDocument(
            id=first_result.id if first_result else "pending",
            file_type=source_type,
            subject=first_result.subject if first_result else "unknown",
            grade=first_result.grade if first_result else None,
            exam_type=first_result.exam_type if first_result else "unknown",
            year=first_result.year if first_result else None,
            source=first_result.source if first_result else None,
            total_questions=len(all_questions),
            generated=first_result.generated if first_result else False,
            duration=first_result.duration if first_result else None,
            metadata=first_result.metadata if first_result else None,
            questions=all_questions,
        )


    def _split_into_chunks(self, questions_list: List[Dict]) -> List[List[Dict]]:
        """Split OCR blocks by raw text size."""
        chunks: List[List[Dict]] = []
        current_chunk: List[Dict] = []
        current_len = 0

        for question in questions_list:
            question_len = len(question.get("raw_text", ""))
            if current_len + question_len > MAX_CHARS_PER_BATCH and current_chunk:
                chunks.append(current_chunk)
                current_chunk = [question]
                current_len = question_len
                continue

            current_chunk.append(question)
            current_len += question_len

        if current_chunk:
            chunks.append(current_chunk)

        return chunks
