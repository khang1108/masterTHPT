"""
Output Structuring Module (Extractor)
--------------------------------------
Sử dụng Gemini 2.5 Flash để chuyển đổi raw OCR text + visual descriptions
thành JSON chuẩn theo Pydantic schema.

Batching Strategy:
    - Gemini Free Tier: 5 requests/phút, ~250k tokens/request
    - Gom TẤT CẢ raw text của mọi trang vào 1 prompt lớn duy nhất
    - Chỉ chia batch khi tổng text vượt ~150k ký tự (~200k tokens)
    - Giữa các batch: sleep 12s để respect rate limit
"""

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

# Dựng Knowledge Base Math Tags List
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
    print(f"[Extractor] Lỗi không thể load knowledge base: {e}")
    VALID_TAGS = ["unknown"]

# Dynamically construct Enum to strictly bound the language model
TopicTagEnum = Enum("TopicTagEnum", {tag.replace(".", "_"): tag for tag in VALID_TAGS})



# ---------------------------------------------------
# PYDANTIC SCHEMAS — matching user's JSON specification
# ---------------------------------------------------

class QuestionNode(BaseModel):
    id: str = Field(description="Unique ID (sẽ bị ghi đè bởi hash UUID).")
    question_index: int = Field(description="Số thứ tự câu hỏi (1-based)")
    type: Literal["multiple_choice", "short_ans", "true_false"] = Field(description="Loại câu hỏi: multiple_choice (trắc nghiệm ABCD), short_ans (điền đáp án ngắn), true_false (đúng/sai)")
    content: str = Field(description="Nội dung câu hỏi dạng plain text")
    content_latex: Optional[str] = Field(None, description="Nội dung câu hỏi encode bằng LaTeX nếu có công thức. CHỈ dùng LaTeX cho công thức toán, KHÔNG vẽ đồ họa.")
    options: Optional[List[str]] = Field(None, description="Danh sách đáp án CHỈ cho multiple_choice, e.g. ['A. ...', 'B. ...', 'C. ...', 'D. ...']. Để null nếu type khác.")
    correct_answer: Optional[str] = Field(None, description="Đáp án đúng nếu có thể xác định, e.g. 'A'")
    has_image: bool = Field(description="True nếu câu hỏi có kèm hình vẽ/đồ thị")
    image_url: Optional[str] = Field(None, description="Đường dẫn ảnh nếu có (trích xuất từ [FIGURE_URL: xxx])")
    difficulty_a: Optional[float] = Field(None, description="IRT discrimination — ĐỂ NULL. Sẽ được tính sau bằng pipeline calibration riêng.")
    difficulty_b: Optional[float] = Field(None, description="IRT difficulty — ĐỂ NULL. Sẽ được tính sau bằng pipeline calibration riêng.")
    topic_tags: List[TopicTagEnum] = Field(description="Tags chủ đề — BẮT BUỘC. Phải chọn CHÍNH XÁC từ danh sách Enum Knowledge Base được cung cấp. TUYỆT ĐỐI KHÔNG đoán mò hay bịa tag mới. Tối thiểu 1 tag.")
    max_score: Optional[float] = Field(None, description="Điểm tối đa cho câu hỏi")


class Section(BaseModel):
    type: Literal["multiple_choice", "short_ans", "true_false"]
    questions: List[QuestionNode]


class ExamDocument(BaseModel):
    id: str = Field(description="UUID định danh đề thi (sẽ bị ghi đè bởi hash)")
    file_type: Literal["image", "pdf"] = Field(description="Nguồn đầu vào")
    subject: str = Field(description="Môn học, e.g. math, physics, chemistry")
    exam_type: str = Field(description="Loại kỳ thi, e.g. THPTQG, V_ACT, HSA, GK1, CK2")
    year: Optional[int] = Field(None, description="Năm thi (nếu có)")
    source: Optional[str] = Field(None, description="Nguồn xuất xứ, e.g. toanmath.com, manual")
    total_questions: int = Field(description="Tổng số câu hỏi")
    duration: Optional[int] = Field(None, description="Thời gian làm bài tính bằng phút (nếu có)")
    metadata: Optional[str] = Field(None, description="Metadata bổ sung dạng JSON string, e.g. '{\"code\": \"MDT001\"}'. Điền null nếu không có.")
    created_at: Optional[str] = Field(None, description="Timestamp tạo bản ghi (sẽ được populate ở local)")
    question_ids: Optional[List[str]] = Field(None, description="Danh sách question_id tham chiếu tới collection questions (sẽ được populate ở local)")
    sections: List[Section]


# ---------------------------------------------------
# CONSTANTS
# ---------------------------------------------------
# Giới hạn ký tự cho 1 batch (~200k tokens ≈ 150k chars tiếng Việt)
MAX_CHARS_PER_BATCH = 150_000
# Thời gian chờ giữa các batch (12s cho 5 req/min)
RATE_LIMIT_SLEEP_SECONDS = 13


class OutputStructuring:
    def __init__(self):
        if not config.GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY chưa được cấu hình! "
                "Hãy kiểm tra file .env hoặc biến môi trường."
            )
        self.client = genai.Client(api_key=config.GEMINI_API_KEY)

    def _build_prompt(
        self,
        questions_list: List[Dict],
        source_type: str = "pdf",
        batch_info: str = ""
    ) -> list:
        """Xây dựng prompt multimodal (text + images) cho Gemini structuring."""
        
        prompt_parts = []
        grouped_content = ""
        
        for i, q in enumerate(questions_list):
            grouped_content += f"\n--- [BLOCK CÂU HỎI {i+1} : ID = {q.get('question_id', '')}] ---\n"
            grouped_content += f"{q.get('raw_text', '')}\n"
            
            # Gắn các file ảnh vật lý vào khối payload
            image_urls = q.get("image_urls", [])
            for abs_path in image_urls:
                try:
                    img = Image.open(abs_path)
                    prompt_parts.append(img)
                except Exception as e:
                    print(f"[Extractor] Error opening image {abs_path}: {e}")

        # Inject danh sách tags hợp lệ từ Knowledge Base vào prompt
        valid_tags_str = "\n".join(f"  - {tag}" for tag in VALID_TAGS)

        text_prompt = f"""Bạn là một chuyên gia phân tích đề thi giáo dục Việt Nam. Nhiệm vụ: nhận nội dung đã được chia block từ đề thi và trích xuất thành JSON chuẩn.

=== THÔNG TIN BATCH ===
{batch_info}
Định dạng file: {source_type}

=== KNOWLEDGE BASE — DANH SÁCH TOPIC TAGS HỢP LỆ (BẮT BUỘC CHỌN TỪ ĐÂY) ===
{valid_tags_str}

=== DỮ LIỆU CÂU HỎI ĐÃ ĐƯỢC GOM NHÓM (GROUPED BLOCKS) ===
{grouped_content}

=== YÊU CẦU TRÍCH XUẤT ===

1. **SỬA LỖI CHÍNH TẢ DO OCR (CỰC KỲ QUAN TRỌNG):**
   OCR thường sai dấu tiếng Việt nghiêm trọng. BẮT BUỘC sửa lỗi trong TẤT CẢ các trường `content`, `options`, VÀ `content_latex`.
   Ví dụ lỗi phổ biến:
   - "duòng" → "đường", "diém" → "điểm", "dúng" → "đúng"
   - "hàm só" → "hàm số", "dáy" → "đáy", "chièu" → "chiều"
   - "nghiêm" → "nghiệm", "khǎng" → "khẳng", "tâp" → "tập"
   - "bién" → "biến", "liēn" → "liên", "dò" → "đồ"
   - "phuong trinh" → "phương trình", "bát" → "bất"
   - "lǎng tru" → "lăng trụ", "mǎt phng" → "mặt phẳng"
   - "thé tích" → "thể tích", "diên tích" → "diện tích"
   - Ký tự Unicode lạ (ε, 嘹, 這, 司) → thay bằng từ đúng theo ngữ cảnh.
   Luôn đoán nghĩa theo ngữ cảnh toán học tiếng Việt để sửa chính xác nhất.

2. **LaTeX CHỈ DÙNG CHO CÔNG THỨC TOÁN INLINE — CẤM VẼ MỌI THỨ:**
   - Chuyển ký hiệu toán học sang LaTeX chuẩn (ví dụ: `$y = ax^4 + bx^2 + c$`).
   - TUYỆT ĐỐI CẤM sinh bất kỳ code nào có mục đích VẼ hoặc TẠO entity trực quan:
     * Đồ thị, biểu đồ (TikZ, pgfplots, tikzpicture, \\draw, \\begin{{axis}})
     * Bảng biến thiên (\\begin{{tabular}}, \\begin{{array}} dùng để vẽ bảng BT)
     * Hình học minh họa (\\begin{{tikzpicture}}, pstricks, \\coordinate)
     * Bảng biểu (\\begin{{table}}, \\begin{{tabular}} phức tạp)
     * Hệ trục tọa độ, sơ đồ, flowchart
     * BẤT KỲ entity đồ họa/HTML/SVG nào khác
   - Hình ảnh sẽ được lấy từ OCR crop sẵn. Nếu câu hỏi có hình → chỉ ghi has_image=true.
   - CHỈ ĐƯỢC PHÉP dùng LaTeX cho: công thức toán inline ($...$), ký hiệu toán (\\frac, \\sqrt, \\int, \\sum, v.v.)

3. Trích xuất thông tin Đề Thi:
   - Xác định môn học (math/physics/chemistry/...) và loại kỳ thi (THPTQG/GK1/CK2/...).
   - Trích xuất `year`, `duration` (phút), `source`. Điền `null` nếu không tìm thấy.

4. Phân tách nội dung câu hỏi và phương án trả lời một cách tự nhiên.

5. Gán nhãn `topic_tags`: BẮT BUỘC chọn từ danh sách KNOWLEDGE BASE ở trên. TUYỆT ĐỐI KHÔNG bịa tag mới.

6. Với mỗi câu hỏi (QuestionNode), tuân thủ Schema:
   - `id`: Giá trị bất kỳ. Hệ thống sẽ ghi đè bằng hash UUID.
   - `question_index`: số thứ tự 1-based (VD: "Câu 19" → 19)
   - `type`: Phân loại chính xác:
     * "multiple_choice" — trắc nghiệm có 4 đáp án A, B, C, D
     * "short_ans" — điền đáp án ngắn (thường ở cuối đề THPTQG)
     * "true_false" — đúng/sai
   - `content`: nội dung ĐÃ SỬA LỖI CHÍNH TẢ. KHÔNG chèn code vẽ.
   - `content_latex`: CHỈ encode công thức toán inline ($...$). KHÔNG vẽ bảng/đồ thị/hình.
   - `options`: CHỈ cho type="multiple_choice". Để null cho short_ans và true_false.
   - `correct_answer`: đáp án đúng nếu có, null nếu không.
   - `has_image`: true nếu có [FIGURE_URL: xxx] hoặc hình vẽ.
   - `image_url`: Copy đường dẫn từ [FIGURE_URL: xxx].
   - `topic_tags`: BẮT BUỘC từ Knowledge Base.

7. ExamDocument: `subject`, `exam_type`, `year`, `source`, `duration`, `total_questions`.

CẤM TUYỆT ĐỐI: Không sinh code LaTeX/HTML/SVG để vẽ bất kỳ thứ gì. Hình ảnh chỉ lấy từ OCR crop.
Trường `id` sẽ bị GHI ĐÈ tự động — KHÔNG cần lo."""

        prompt_parts.insert(0, text_prompt)
        return prompt_parts

    @staticmethod
    def _generate_exam_id(questions_list: List[Dict]) -> str:
        """
        Sinh exam_id bằng uuid5 hash từ toàn bộ raw_text OCR.
        Đảm bảo cùng file PDF luôn ra cùng 1 exam_id.
        """
        total_raw = "".join(q.get("raw_text", "") for q in questions_list)
        return str(uuid.uuid5(uuid.NAMESPACE_OID, total_raw))

    @staticmethod
    def _generate_question_id(exam_id: str, question_index: int) -> str:
        """
        Sinh question_id bằng uuid5 hash từ exam_id + question_index.
        Đảm bảo unique, ổn định, độc lập với Gemini response.
        """
        seed = f"{exam_id}_{question_index}"
        return str(uuid.uuid5(uuid.NAMESPACE_OID, seed))

    def _assign_hash_ids(self, doc: ExamDocument, exam_id: str) -> ExamDocument:
        """
        Ghi đè toàn bộ ID từ Gemini bằng hash-based UUID.
        Gán exam_id, question_ids, và created_at.
        """
        doc.id = exam_id
        doc.created_at = datetime.now(timezone.utc).isoformat()

        all_question_ids = []
        for sec in doc.sections:
            for q in sec.questions:
                q.id = self._generate_question_id(exam_id, q.question_index)
                all_question_ids.append(q.id)

        # Gán danh sách question_ids vào exam
        doc.question_ids = all_question_ids

        # Cập nhật total_questions cho chính xác
        actual_count = sum(len(s.questions) for s in doc.sections)
        doc.total_questions = actual_count

        return doc

    def structure_output(
        self,
        questions_list: List[Dict],
        source_type: str = "pdf"
    ) -> ExamDocument:
        """
        Gọi Gemini để chuyển list các raw chunk → ExamDocument JSON.
        Sau đó ghi đè toàn bộ ID bằng hash-based UUID.
        """
        # Sinh exam_id ổn định từ nội dung raw OCR
        exam_id = self._generate_exam_id(questions_list)
        print(f"[Extractor] 🔑 Exam ID (hash): {exam_id}")

        # Đếm tổng lượng ký tự trung bình
        total_chars = sum(len(q.get("raw_text", "")) for q in questions_list)

        if total_chars <= MAX_CHARS_PER_BATCH:
            # ====== SINGLE BATCH ======
            print(f"[Extractor] Single batch: {len(questions_list)} câu hỏi ({total_chars:,} ký tự) → gọi Gemini Multimodal 1 lần")
            doc = self._call_gemini(questions_list, source_type)
        else:
            # ====== MULTI BATCH (nếu quá dài) ======
            doc = self._process_multi_batch(questions_list, source_type)

        # Ghi đè toàn bộ ID bằng hash (Mặc kệ kết quả Gemini)
        doc = self._assign_hash_ids(doc, exam_id)

        print(f"[Extractor] ✅ Hash IDs đã được gán: exam={doc.id}, questions={doc.total_questions} câu")
        return doc

    def _call_gemini(
        self,
        questions_list: List[Dict],
        source_type: str,
        batch_info: str = ""
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
        self,
        questions_list: List[Dict],
        source_type: str
    ) -> ExamDocument:
        """
        Chia list câu hỏi thành nhiều batch, gọi Gemini cho từng batch,
        rồi merge tất cả sections lại thành 1 ExamDocument.
        """
        chunks = self._split_into_chunks(questions_list)
        total_batches = len(chunks)

        print(f"[Extractor] Multi-batch: {len(questions_list)} câu hỏi → {total_batches} batches")

        all_sections: Dict[str, List] = {"multiple_choice": [], "essay": []}
        first_result: ExamDocument | None = None

        for i, chunk in enumerate(chunks):
            batch_info = f"Batch {i + 1}/{total_batches}"
            print(f"[Extractor] Đang xử lý {batch_info} ({len(chunk)} câu hỏi)...")

            if i > 0:
                # Rate limit: chờ giữa các batch
                print(f"[Extractor] ⏳ Chờ {RATE_LIMIT_SLEEP_SECONDS}s (rate limit)...")
                time.sleep(RATE_LIMIT_SLEEP_SECONDS)

            result = self._call_gemini(chunk, source_type, batch_info)

            if first_result is None:
                first_result = result

            # Gom câu hỏi từ mỗi batch
            for section in result.sections:
                all_sections[section.type].extend(section.questions)

        # Merge thành 1 ExamDocument duy nhất
        merged_sections = []
        if all_sections["multiple_choice"]:
            merged_sections.append(Section(
                type="multiple_choice",
                questions=all_sections["multiple_choice"]
            ))
        if all_sections["essay"]:
            merged_sections.append(Section(
                type="essay",
                questions=all_sections["essay"]
            ))

        total_q = sum(len(s.questions) for s in merged_sections)

        return ExamDocument(
            id=first_result.id if first_result else "pending",
            file_type=source_type,
            subject=first_result.subject if first_result else "unknown",
            exam_type=first_result.exam_type if first_result else "unknown",
            year=first_result.year if first_result else None,
            source=first_result.source if first_result else None,
            total_questions=total_q,
            duration=first_result.duration if first_result else None,
            metadata=first_result.metadata if first_result else None,
            sections=merged_sections
        )

    def _split_into_chunks(self, questions_list: List[Dict]) -> List[List[Dict]]:
        """
        Chia danh sách câu hỏi thành các chunk sao cho tổng ký tự thô
        mỗi chunk nhỏ hơn MAX_CHARS_PER_BATCH.
        """
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
