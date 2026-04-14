import time
import uuid
import os
import json
import hashlib
from datetime import datetime, timezone
from enum import Enum
from PIL import Image
from google import genai
from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any
from config import config

# Load Knowledge Base tags hợp lệ
kb_path = os.path.join(os.path.dirname(__file__), "math_knowledge_base.json")
VALID_TAGS = []

try:
    with open(kb_path, "r", encoding="utf-8") as f:
        kb_data = json.load(f)
    for node in kb_data.get("nodes", []):
        if node["id"] not in VALID_TAGS:
            VALID_TAGS.append(node["id"])
        for p in node.get("prerequisites", []):
            if p not in VALID_TAGS:
                VALID_TAGS.append(p)
except Exception as e:
    print(f"[Extractor] Lỗi load knowledge base: {e}")
    VALID_TAGS = ["unknown"]

TopicTagEnum = Enum("TopicTagEnum", {tag.replace(".", "_"): tag for tag in VALID_TAGS})


# Pydantic schemas
class QuestionNode(BaseModel):
    id: str = Field(description="Unique ID (sẽ bị ghi đè bởi hash UUID).")
    question_index: int = Field(description="Số thứ tự câu hỏi (1-based)")
    type: Literal["multiple_choice", "short_ans", "true_false"] = Field(description="Loại câu hỏi")
    content: str = Field(description="Nội dung câu hỏi dạng plain text")
    content_latex: Optional[str] = Field(None, description="LaTeX cho công thức toán (KHÔNG vẽ đồ họa)")
    options: Optional[List[str]] = Field(None, description="Đáp án CHỈ cho multiple_choice")
    correct_answer: Optional[str] = Field(None, description="Đáp án đúng nếu xác định được")
    has_image: bool = Field(description="True nếu có hình vẽ/đồ thị")
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
    generated: bool = Field(description="Định nghĩa đề thi được gen ra")
    duration: Optional[int] = Field(None, description="Thời gian làm bài (phút)")
    metadata: Optional[str] = Field(None, description="Metadata bổ sung")
    created_at: Optional[str] = Field(None, description="Timestamp tạo bản ghi")
    questions: List[QuestionNode]


MAX_CHARS_PER_BATCH = 150_000
RATE_LIMIT_SLEEP_SECONDS = 13


class OutputStructuring:
    def __init__(self):
        if not config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY chưa được cấu hình!")
        self.client = genai.Client(api_key=config.GEMINI_API_KEY)

    def _build_prompt(self, questions_list: List[Dict], source_type: str = "pdf", batch_info: str = "") -> list:
        """Xây dựng prompt multimodal cho Gemini structuring."""
        prompt_parts = []
        grouped_content = ""

        for i, q in enumerate(questions_list):
            grouped_content += f"\n--- [BLOCK CÂU HỎI {i+1} : ID = {q.get('question_id', '')}] ---\n"
            grouped_content += f"{q.get('raw_text', '')}\n"

            image_urls = q.get("image_urls", [])
            for abs_path in image_urls:
                try:
                    img = Image.open(abs_path)
                    prompt_parts.append(img)
                except Exception as e:
                    print(f"[Extractor] Error opening image {abs_path}: {e}")

        valid_tags_str = "\n".join(f"  - {tag}" for tag in VALID_TAGS)

        text_prompt = f"""Bạn là chuyên gia phân tích đề thi giáo dục Việt Nam. Trích xuất nội dung đã chia block thành JSON chuẩn.

{batch_info}
File: {source_type}

=== TOPIC TAGS HỢP LỆ (BẮT BUỘC chọn từ đây, CẤM bịa tag mới) ===
{valid_tags_str}

=== DỮ LIỆU ĐẦU VÀO ===
{grouped_content}

=== QUY TẮC CHUNG ===

1. **Tiếng Việt có dấu đầy đủ (CỰC KỲ QUAN TRỌNG):**
   - Mọi output tiếng Việt PHẢI có dấu chuẩn xác. Chỉ tên biến/field đặt tiếng Anh.
   - Ví dụ: "Trường THPT Lê Hồng Phong" ✔️ | "Truong THPT Le Hong Phong" ❌
   - Viết rõ ràng: HK1 → "Kiểm tra học kỳ 1", HK2 → "Kiểm tra học kỳ 2", GK → "Kiểm tra giữa kỳ"
   - THPTQG → "Thi tốt nghiệp THPT Quốc gia", CK1 → "Kiểm tra cuối kỳ 1"

2. **Sửa lỗi chính tả OCR:** OCR thường sai dấu tiếng Việt. Sửa trong TẤT CẢ `content`, `options`, `content_latex`.
   - "duòng"→"đường", "diém"→"điểm", "hàm só"→"hàm số", "nghiêm"→"nghiệm", "phuong trinh"→"phương trình"
   - "lǎng tru"→"lăng trụ", "mǎt phng"→"mặt phẳng", "thé tích"→"thể tích", "diên tích"→"diện tích"
   - Ký tự Unicode lạ (ε, 嘹, 這, 司) → thay bằng từ đúng theo ngữ cảnh toán học.

3. **LaTeX:** CHỈ dùng cho công thức toán inline ($...$). CẤM sinh TikZ, pgfplots, tabular, array, tikzpicture, draw, hay bất kỳ code vẽ đồ họa nào. Hình ảnh lấy từ OCR crop sẵn.

=== SCHEMA CÂU HỎI (QuestionNode) ===
- `id`: giá trị bất kỳ (hệ thống ghi đè)
- `question_index`: số thứ tự 1-based ("Câu 19" → 19)
- `type`: "multiple_choice" | "short_ans" | "true_false"
- `content`: nội dung đã sửa lỗi, tiếng Việt có dấu
- `content_latex`: công thức toán inline. KHÔNG vẽ bảng/đồ thị/hình
- `options`: chỉ cho multiple_choice, null cho loại khác
- `correct_answer`: đáp án đúng hoặc null
- `has_image`: true nếu có [FIGURE_URL]
- `image_url`: copy đường dẫn từ [FIGURE_URL: xxx]
- `topic_tags`: BẮT BUỘC chọn từ Knowledge Base

=== SCHEMA ĐỀ THI (ExamDocument) ===
- `subject`: tên môn tiếng Việt có dấu ("Toán", "Vật lý", "Hóa học")
- `grade`: khối lớp (10, 11, 12) hoặc null
- `exam_type`: viết đầy đủ tiếng Việt có dấu ("Kiểm tra giữa kỳ 1", "Thi tốt nghiệp THPT Quốc gia")
- `source`: tên trường/sở đầy đủ dấu ("Sở GDĐT Hà Nội", "Trường THPT chuyên Lê Hồng Phong")
- `year`, `duration`, `total_questions`: trích xuất hoặc null

Trường `id` sẽ bị GHI ĐÈ tự động."""

        prompt_parts.insert(0, text_prompt)
        return prompt_parts

    @staticmethod
    def _generate_exam_id(questions_list: List[Dict]) -> str:
        """Sinh exam_id ổn định bằng uuid5 hash từ raw OCR text."""
        total_raw = "".join(q.get("raw_text", "") for q in questions_list)
        return str(uuid.uuid5(uuid.NAMESPACE_OID, total_raw))

    @staticmethod
    def _generate_question_id(exam_id: str, question_index: int) -> str:
        """Sinh question_id bằng uuid5 hash từ exam_id + index."""
        seed = f"{exam_id}_{question_index}"
        return str(uuid.uuid5(uuid.NAMESPACE_OID, seed))

    def _assign_hash_ids(self, doc: ExamDocument, exam_id: str) -> ExamDocument:
        """Ghi đè toàn bộ ID Gemini bằng hash-based UUID."""
        doc.id = exam_id
        doc.created_at = datetime.now(timezone.utc).isoformat()
        for q in doc.questions:
            q.id = self._generate_question_id(exam_id, q.question_index)
        doc.total_questions = len(doc.questions)
        return doc

    def structure_output(
        self, questions_list: List[Dict], source_type: str = "pdf"
    ) -> ExamDocument:
        """Gọi Gemini chuyển raw chunks → ExamDocument."""
        exam_id = self._generate_exam_id(questions_list)
        print(f"[Extractor] Exam ID (hash): {exam_id}")

        total_chars = sum(len(q.get("raw_text", "")) for q in questions_list)

        if total_chars <= MAX_CHARS_PER_BATCH:
            print(f"[Extractor] Single batch: {len(questions_list)} câu ({total_chars:,} chars)")
            doc = self._call_gemini(questions_list, source_type)
        else:
            doc = self._process_multi_batch(questions_list, source_type)

        doc = self._assign_hash_ids(doc, exam_id)
        print(f"[Extractor] Hash IDs assigned: exam={doc.id}, questions={doc.total_questions}")
        return doc

    def _call_gemini(
        self, questions_list: List[Dict], source_type: str, batch_info: str = ""
    ) -> ExamDocument:
        """Gọi Gemini API 1 lần với structured output."""
        prompt_parts = self._build_prompt(questions_list, source_type, batch_info)
        response = self.client.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=prompt_parts,
            config=genai.types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ExamDocument,
                temperature=0.1
            ),
        )
        return ExamDocument.model_validate_json(response.text)

    def _process_multi_batch(
        self, questions_list: List[Dict], source_type: str
    ) -> ExamDocument:
        """Chia thành nhiều batch, gọi Gemini từng batch, merge lại."""
        chunks = self._split_into_chunks(questions_list)
        total_batches = len(chunks)
        print(f"[Extractor] Multi-batch: {len(questions_list)} câu → {total_batches} batches")

        all_questions: List[QuestionNode] = []
        first_result: ExamDocument | None = None

        for i, chunk in enumerate(chunks):
            batch_info = f"Batch {i + 1}/{total_batches}"
            print(f"{batch_info} ({len(chunk)} câu)...")

            if i > 0:
                time.sleep(RATE_LIMIT_SLEEP_SECONDS)

            result = self._call_gemini(chunk, source_type, batch_info)
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
            duration=first_result.duration if first_result else None,
            metadata=first_result.metadata if first_result else None,
            questions=all_questions,
        )

    def _split_into_chunks(self, questions_list: List[Dict]) -> List[List[Dict]]:
        """Chia danh sách câu hỏi theo MAX_CHARS_PER_BATCH."""
        chunks: List[List[Dict]] = []
        current_chunk: List[Dict] = []
        current_len = 0

        for q in questions_list:
            q_len = len(q.get("raw_text", ""))
            if current_len + q_len > MAX_CHARS_PER_BATCH and current_chunk:
                chunks.append(current_chunk)
                current_chunk = [q]
                current_len = q_len
            else:
                current_chunk.append(q)
                current_len += q_len

        if current_chunk:
            chunks.append(current_chunk)

        return chunks
