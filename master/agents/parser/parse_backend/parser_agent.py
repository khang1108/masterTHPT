import os
import time
import base64
import requests
from typing import Optional, List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image

from pdf_splitter import split_pdf_to_images
from grouping_script import group_blocks_into_questions
from extractor import OutputStructuring
from config import config
# from mongo_client import MongoDBClient  # Tạm tắt DB cho testing

# ========================================
# CẤU HÌNH TỐI ƯU OCR
# ========================================
MAX_OCR_WIDTH = 1240     # Resize ảnh trước khi gửi OCR (A4 ratio)
MAX_OCR_HEIGHT = 1754    # Đủ lớn để OCR chính xác, đủ nhỏ để nhanh
OCR_CONCURRENCY = 4      # Số trang gửi song song cùng lúc


class ParserAgent:
    """
    ParserAgent — Lõi xử lý pipeline chính, nhận PDF/Ảnh và xuất ra JSON.
    Theo chuẩn kiến trúc 3 bước:
        1. Gọi Kaggle OCR PP-StructureV3.
        2. Dùng Regex Grouping chia các câu.
        3. Dùng Gemini structurize thành schema JSON khép kín.
    """
    
    def __init__(self, output_dir: str = "parsed_results"):
        """
        Khởi tạo ParserAgent.
        Args:
            output_dir (str): Thư mục để lưu các file JSON đầu ra.
        """
        self.output_dir = output_dir
        self.structurer = OutputStructuring()
        # self.db_client = MongoDBClient()  # Tạm tắt DB cho testing
        
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            print(f"[ParserAgent] 📁 Đã tạo thư mục lưu trữ: {self.output_dir}")

    @staticmethod
    def _resize_image_for_ocr(image_path: str) -> str:
        """
        Resize ảnh xuống max MAX_OCR_WIDTH x MAX_OCR_HEIGHT nếu vượt quá.
        Trả về đường dẫn file đã resize (ghi đè file gốc để tiết kiệm đĩa).
        """
        try:
            with Image.open(image_path) as img:
                w, h = img.size
                if w <= MAX_OCR_WIDTH and h <= MAX_OCR_HEIGHT:
                    return image_path  # Không cần resize
                
                # Tính tỉ lệ scale giữ aspect ratio
                scale = min(MAX_OCR_WIDTH / w, MAX_OCR_HEIGHT / h)
                new_w = int(w * scale)
                new_h = int(h * scale)
                
                img_resized = img.resize((new_w, new_h), Image.LANCZOS)
                img_resized.save(image_path, optimize=True)
                
            return image_path
        except Exception as e:
            print(f"    [!] Lỗi resize {os.path.basename(image_path)}: {e}")
            return image_path  # Trả về gốc nếu lỗi

    def _send_image_to_kaggle(self, image_path: str) -> Optional[Dict]:
        """Gửi ảnh lên endpoint Kaggle để lấy bboxes."""
        api_url = f"{config.KAGGLE_NGROK_URL.rstrip('/')}/extract_ocr"

        try:
            with open(image_path, 'rb') as f:
                files = {'image': (os.path.basename(image_path), f, 'image/png')}
                # Timeout cao vì OCR có thể chạy mất nhiều thời gian
                response = requests.post(api_url, files=files, timeout=300)
                response.raise_for_status()

            data = response.json()
            if data.get("status") != "success":
                print(f"    [!] Kaggle trả về lỗi cho {os.path.basename(image_path)}: {data}")
                return None
            return data

        except requests.exceptions.ConnectionError:
            print(f"    [!] Không thể kết nối tới Kaggle Service tại: {api_url}")
            return None
        except Exception as e:
            print(f"    [!] Lỗi khi gửi {os.path.basename(image_path)}: {e}")
            return None

    def _process_single_page(self, page_num: int, img_path: str, base_name: str, images_dir: str) -> List[Dict]:
        """
        Xử lý 1 trang: resize → OCR → grouping → trả về danh sách câu hỏi.
        Hàm này thread-safe, dùng cho ThreadPoolExecutor.
        """
        print(f"    📤 Trang {page_num}: Đang gửi OCR...")
        
        # Resize trước khi gửi
        self._resize_image_for_ocr(img_path)
        
        result = self._send_image_to_kaggle(img_path)
        if not result:
            print(f"    ⚠️ Trang {page_num}: Gặp lỗi OCR. Bỏ qua.")
            return []
            
        parsing_blocks = result.get("parsing_blocks", [])
        visual_crops = result.get("visual_base64_crops", {})
        
        # Gán key unique cho mỗi trang để chống đụng độ
        for block in parsing_blocks:
            if 'block_id' in block:
                block['block_id'] = f"p{page_num}_{block['block_id']}"
                
        saved_crop_paths = {}
        for k, b64_data in visual_crops.items():
            fig_id = f"p{page_num}_{k}"
            
            # Tự động chuyển Base64 thành File vật lý nằm trên đĩa cứng
            img_bytes = base64.b64decode(b64_data)
            
            # Flatten filename để tránh lỗi Subdirectory (k chứa dấu "/")
            safe_k = k.replace("/", "_").replace("\\", "_")
            img_filename = f"p{page_num}_{safe_k}.png"
            img_filepath = os.path.join(images_dir, img_filename)
            
            with open(img_filepath, "wb") as f:
                f.write(img_bytes)
                
            # Tạo URL rút gọn cho web frontend
            web_url = f"/images/{base_name}/{img_filename}"
            saved_crop_paths[fig_id] = {
                "abs_path": os.path.abspath(img_filepath),
                "web_url": web_url
            }
        
        page_qs = group_blocks_into_questions(parsing_blocks, saved_crop_paths)
        print(f"    ✓ Trang {page_num}: Bóc được {len(page_qs)} câu hỏi thô.")
        return page_qs

    def process(self, file_path: str) -> Optional[str]:
        """
        Khởi chạy luồng xử lý toàn diện cho file_path.
        Lưu kết quả ra file JSON và trả về đường dẫn file đó.
        """
        if not os.path.exists(file_path):
            print(f"[ParserAgent] ❌ Không tìm thấy file: {file_path}")
            return None

        ext = os.path.splitext(file_path)[1].lower()
        if ext not in config.ALLOWED_EXTENSIONS:
            print(f"[ParserAgent] ❌ Định dạng '{ext}' không được hỗ trợ.")
            return None
        
        # ========================================
        # BƯỚC 1: TIỀN XỬ LÝ (Tách/Chuẩn bị ảnh)
        # ========================================
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        images_dir = os.path.join(self.output_dir, "images", base_name)
        if not os.path.exists(images_dir):
            os.makedirs(images_dir)
            
        source_type = "pdf" if ext == ".pdf" else "image"
        print(f"\n{'='*60}")
        print(f"🚀 PARSER AGENT — KÍCH HOẠT (Mode: {source_type.upper()})")
        print(f"📄 Target: {os.path.basename(file_path)}")
        print(f"🖼️  Lưu ảnh đồ thị tại: {images_dir}")
        print(f"⚡ OCR concurrency: {OCR_CONCURRENCY} trang song song")
        print(f"📐 Max resolution: {MAX_OCR_WIDTH}x{MAX_OCR_HEIGHT}px")
        print(f"{'='*60}")
        
        if source_type == "pdf":
            image_paths = split_pdf_to_images(file_path)
        else:
            image_paths = [os.path.abspath(file_path)]
            
        print(f"[ParserAgent] ✓ Bước 1: Chuẩn bị xong {len(image_paths)} ảnh trang.")
        
        # ========================================
        # BƯỚC 2: KAGGLE OCR & GỘP GROUPING (SONG SONG)
        # ========================================
        print(f"\n[ParserAgent] 🌐 Bước 2: Giao tiếp OCR & Regex Grouping (song song {OCR_CONCURRENCY} workers)...")
        
        t_start = time.time()
        
        # Dùng ThreadPoolExecutor để gửi song song 4 trang cùng lúc
        all_grouped_questions = []
        page_results = {}  # {page_num: [questions]}

        with ThreadPoolExecutor(max_workers=OCR_CONCURRENCY) as executor:
            futures = {}
            for i, img_path in enumerate(image_paths):
                page_num = i + 1
                future = executor.submit(
                    self._process_single_page,
                    page_num, img_path, base_name, images_dir
                )
                futures[future] = page_num
            
            for future in as_completed(futures):
                page_num = futures[future]
                try:
                    page_qs = future.result()
                    page_results[page_num] = page_qs
                except Exception as e:
                    print(f"    ❌ Trang {page_num}: Exception - {e}")
                    page_results[page_num] = []

        # Gộp theo thứ tự trang (quan trọng cho question_index chính xác)
        for page_num in sorted(page_results.keys()):
            all_grouped_questions.extend(page_results[page_num])

        t_elapsed = time.time() - t_start
            
        if not all_grouped_questions:
            print("\n[ParserAgent] ❌ Thất bại: Không thu được câu hỏi nào từ file đầu vào.")
            return None
            
        print(f"\n[ParserAgent] ✓ Bước 2: Gom xong {len(all_grouped_questions)} chunks trong {t_elapsed:.1f}s.")

        # ========================================
        # BƯỚC 3: GEMINI STRUCTURING & SAVE
        # ========================================
        print(f"\n[ParserAgent] 🧠 Bước 3: Cấu trúc hóa trí tuệ Pydantic...")
        
        try:
            exam_document = self.structurer.structure_output(
                questions_list=all_grouped_questions,
                source_type=source_type
            )
            
            # Tính số lượng thực tế
            actual_q_count = sum(len(sec.questions) for sec in exam_document.sections)
            
            print(f"\n[ParserAgent] ✓ Hoàn tất Structuring!")
            print(f"    📊 Môn học:   {exam_document.subject}")
            print(f"    📝 Số Lượng:  {actual_q_count} câu (Báo Cáo: {exam_document.total_questions})")
            
            # ========================================
            # XUẤT 2 FILE JSON RIÊNG BIỆT (exam + questions)
            # ========================================
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            
            # --- FILE 1: _exam.json (Bảng exams — không chứa sections/questions) ---
            exam_dict = exam_document.model_dump()
            exam_dict.pop("sections", None)  # Bỏ sections ra khỏi bảng exam
            exam_dict.pop("file_type", None)  # Không cần lưu vào DB
            
            exam_filepath = os.path.join(self.output_dir, f"{base_name}_exam.json")
            with open(exam_filepath, "w", encoding="utf-8") as f:
                import json as json_mod
                json_mod.dump(exam_dict, f, ensure_ascii=False, indent=2)
            print(f"[ParserAgent] 💾 Bảng EXAMS  → {exam_filepath}")
            
            # --- FILE 2: _questions.json (Bảng questions — flat array) ---
            questions_list_out = []
            for sec in exam_document.sections:
                for q in sec.questions:
                    q_dict = q.model_dump()
                    # Serialize TopicTagEnum thành string value
                    if q_dict.get("topic_tags"):
                        q_dict["topic_tags"] = [
                            tag.value if hasattr(tag, 'value') else str(tag)
                            for tag in q_dict["topic_tags"]
                        ]
                    questions_list_out.append(q_dict)
            
            questions_filepath = os.path.join(self.output_dir, f"{base_name}_questions.json")
            with open(questions_filepath, "w", encoding="utf-8") as f:
                import json as json_mod
                json_mod.dump(questions_list_out, f, ensure_ascii=False, indent=2)
            print(f"[ParserAgent] 💾 Bảng QUESTIONS → {questions_filepath} ({len(questions_list_out)} docs)")
            
            # --- FILE 3: _parsed.json (Combined — backward compat) ---
            combined_filepath = os.path.join(self.output_dir, f"{base_name}_parsed.json")
            with open(combined_filepath, "w", encoding="utf-8") as f:
                f.write(exam_document.model_dump_json(indent=2))
            print(f"[ParserAgent] 💾 Combined   → {combined_filepath}")
            
            # === MongoDB (tạm tắt cho testing) ===
            # if getattr(self, "db_client", None) and getattr(self.db_client, "client", None):
            #     print(f"[ParserAgent] 🌐 Đang chuẩn bị đồng bộ hoá JSON lên MongoDB...")
            #     self.db_client.push_exam(combined_filepath)
                
            return combined_filepath
            
        except Exception as e:
            print(f"\n[ParserAgent] ❌ Exception tại Bước 3: {e}")
            import traceback
            traceback.print_exc()
            return None
