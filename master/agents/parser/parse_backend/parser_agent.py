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

# OCR config
MAX_OCR_WIDTH = 1240
MAX_OCR_HEIGHT = 1754
OCR_CONCURRENCY = 4


class ParserAgent:

    def __init__(self, output_dir: str = "parsed_results"):
        self.output_dir = output_dir
        self.structurer = OutputStructuring()

        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            print(f"Đã tạo thư mục: {self.output_dir}")

    @staticmethod
    def _resize_image_for_ocr(image_path: str) -> str:
        """Resize ảnh xuống max resolution nếu vượt quá, giữ aspect ratio."""
        try:
            with Image.open(image_path) as img:
                w, h = img.size
                if w <= MAX_OCR_WIDTH and h <= MAX_OCR_HEIGHT:
                    return image_path

                scale = min(MAX_OCR_WIDTH / w, MAX_OCR_HEIGHT / h)
                new_w, new_h = int(w * scale), int(h * scale)
                img_resized = img.resize((new_w, new_h), Image.LANCZOS)
                img_resized.save(image_path, optimize=True)

            return image_path
        except Exception as e:
            print(f"Lỗi resize {os.path.basename(image_path)}: {e}")
            return image_path

    def _send_image_to_kaggle(self, image_path: str) -> Optional[Dict]:
        api_url = f"{config.KAGGLE_NGROK_URL.rstrip('/')}/extract_ocr"

        try:
            with open(image_path, 'rb') as f:
                files = {'image': (os.path.basename(image_path), f, 'image/png')}
                response = requests.post(api_url, files=files, timeout=300)
                response.raise_for_status()

            data = response.json()
            if data.get("status") != "success":
                print(f"Lỗi cho {os.path.basename(image_path)}: {data}")
                return None
            return data

        except requests.exceptions.ConnectionError:
            print(f"Không thể kết nối Kaggle: {api_url}")
            return None
        except Exception as e:
            print(f"Lỗi gửi {os.path.basename(image_path)}: {e}")
            return None

    def _process_single_page(self, page_num: int, img_path: str, base_name: str, images_dir: str) -> List[Dict]:
        print(f"Trang {page_num}: Đang gửi OCR...")
        self._resize_image_for_ocr(img_path)

        result = self._send_image_to_kaggle(img_path)
        if not result:
            print(f"Trang {page_num}: Lỗi OCR, bỏ qua.")
            return []

        parsing_blocks = result.get("parsing_blocks", [])
        visual_crops = result.get("visual_base64_crops", {})

        for block in parsing_blocks:
            if 'block_id' in block:
                block['block_id'] = f"p{page_num}_{block['block_id']}"

        saved_crop_paths = {}
        for k, b64_data in visual_crops.items():
            fig_id = f"p{page_num}_{k}"
            img_bytes = base64.b64decode(b64_data)

            safe_k = k.replace("/", "_").replace("\\", "_")
            img_filename = f"p{page_num}_{safe_k}.png"
            img_filepath = os.path.join(images_dir, img_filename)

            with open(img_filepath, "wb") as f:
                f.write(img_bytes)

            web_url = f"/images/{base_name}/{img_filename}"
            saved_crop_paths[fig_id] = {
                "abs_path": os.path.abspath(img_filepath),
                "web_url": web_url
            }

        page_qs = group_blocks_into_questions(parsing_blocks, saved_crop_paths)
        print(f"    ✓ Trang {page_num}: {len(page_qs)} câu hỏi thô.")
        return page_qs

    def process(self, file_path: str) -> Optional[str]:
        if not os.path.exists(file_path):
            print(f"Không tìm thấy file: {file_path}")
            return None

        ext = os.path.splitext(file_path)[1].lower()
        if ext not in config.ALLOWED_EXTENSIONS:
            print(f"Định dạng '{ext}' không hỗ trợ.")
            return None

        # Bước 1: Chuẩn bị ảnh
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        images_dir = os.path.join(self.output_dir, "images", base_name)
        if not os.path.exists(images_dir):
            os.makedirs(images_dir)

        source_type = "pdf" if ext == ".pdf" else "image"
        print(f"\n{'='*60}")
        print(f"{source_type.upper()} | {os.path.basename(file_path)}")
        print(f"OCR: {OCR_CONCURRENCY} workers | Max: {MAX_OCR_WIDTH}x{MAX_OCR_HEIGHT}px")
        print(f"{'='*60}")

        if source_type == "pdf":
            image_paths = split_pdf_to_images(file_path)
        else:
            image_paths = [os.path.abspath(file_path)]

        print(f"Bước 1: {len(image_paths)} ảnh trang.")

        # Bước 2: OCR + Grouping song song
        t_start = time.time()

        all_grouped_questions = []
        page_results = {}

        with ThreadPoolExecutor(max_workers=OCR_CONCURRENCY) as executor:
            futures = {}
            for i, img_path in enumerate(image_paths):
                page_num = i + 1
                future = executor.submit(self._process_single_page, page_num, img_path, base_name, images_dir)
                futures[future] = page_num

            for future in as_completed(futures):
                page_num = futures[future]
                try:
                    page_results[page_num] = future.result()
                except Exception as e:
                    print(f"Trang {page_num}: {e}")
                    page_results[page_num] = []

        for page_num in sorted(page_results.keys()):
            all_grouped_questions.extend(page_results[page_num])

        t_elapsed = time.time() - t_start

        if not all_grouped_questions:
            print("\n Không thu được câu hỏi nào.")
            return None

        print(f"\n Bước 2: {len(all_grouped_questions)} chunks trong {t_elapsed:.1f}s.")

        # Bước 3: Gemini structuring & save JSON
        print(f"\n Bước 3:  Data Structuring")

        try:
            exam_document = self.structurer.structure_output(
                questions_list=all_grouped_questions,
                source_type=source_type
            )

            actual_q_count = sum(len(sec.questions) for sec in exam_document.sections)
            print(f"\n {exam_document.subject} | {actual_q_count} câu")

            # Xuất _exam.json
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            exam_dict = exam_document.model_dump()
            exam_dict.pop("sections", None)
            exam_dict.pop("file_type", None)

            exam_filepath = os.path.join(self.output_dir, f"{base_name}_exam.json")
            with open(exam_filepath, "w", encoding="utf-8") as f:
                import json as json_mod
                json_mod.dump(exam_dict, f, ensure_ascii=False, indent=2)
            print(f"EXAMS → {exam_filepath}")

            # Xuất _questions.json
            questions_list_out = []
            for sec in exam_document.sections:
                for q in sec.questions:
                    q_dict = q.model_dump()
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
            print(f"QUESTIONS → {questions_filepath} ({len(questions_list_out)} docs)")

            # Xuất _parsed.json (combined)
            combined_filepath = os.path.join(self.output_dir, f"{base_name}_parsed.json")
            with open(combined_filepath, "w", encoding="utf-8") as f:
                f.write(exam_document.model_dump_json(indent=2))
            print(f"Combined → {combined_filepath}")

            return combined_filepath

        except Exception as e:
            print(f"\n Exception Bước 3: {e}")
            import traceback
            traceback.print_exc()
            return None
