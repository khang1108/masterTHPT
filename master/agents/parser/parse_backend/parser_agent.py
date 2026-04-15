import base64
import io
import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional

import requests
from PIL import Image, ImageStat

from config import config
from extractor import ExamDocument, OutputStructuring
from grouping_script import group_blocks_into_questions
from mongo_client import MongoDBClient
from pdf_splitter import split_pdf_to_images


MAX_OCR_WIDTH = 1240
MAX_OCR_HEIGHT = 1754
OCR_CONCURRENCY = 4
MIN_SAVED_IMAGE_WIDTH = 300
MIN_SAVED_IMAGE_HEIGHT = 35
MAX_SAVED_IMAGE_WIDTH = 500
MAX_SAVED_IMAGE_HEIGHT = 500
WHITE_PIXEL_THRESHOLD = 247
MIN_NON_WHITE_RATIO = 0.003
MIN_GRAYSCALE_RANGE = 10
DISPLAY_ASSET_KINDS = {"image", "table", "chart", "visual"}


class ParserAgent:

    def __init__(self, output_dir: str = "parsed_results"):
        self.output_dir = output_dir
        self.structurer = OutputStructuring()
        self.mongo_client = MongoDBClient()
        self.parser_output: Optional[ExamDocument] = None

        os.makedirs(self.output_dir, exist_ok=True)


    @staticmethod
    def _resize_image_for_ocr(image_path: str) -> str:
        """Resize large pages before OCR."""
        try:
            with Image.open(image_path) as image:
                width, height = image.size
                if width <= MAX_OCR_WIDTH and height <= MAX_OCR_HEIGHT:
                    return image_path

                scale = min(MAX_OCR_WIDTH / width, MAX_OCR_HEIGHT / height)
                resized = image.resize(
                    (int(width * scale), int(height * scale)),
                    Image.LANCZOS,
                )
                resized.save(image_path, optimize=True)
            return image_path
        except Exception as error:
            print(f"[Parser] Resize failed for {os.path.basename(image_path)}: {error}")
            return image_path


    def _send_image_to_kaggle(self, image_path: str) -> Optional[Dict]:
        api_url = f"{config.KAGGLE_NGROK_URL.rstrip('/')}/extract_ocr"

        try:
            with open(image_path, "rb") as file:
                files = {"image": (os.path.basename(image_path), file, "image/png")}
                response = requests.post(api_url, files=files, timeout=300)
            response.raise_for_status()

            payload = response.json()
            if payload.get("status") != "success":
                print(f"[Parser] OCR failed for {os.path.basename(image_path)}")
                return None

            return payload
        except requests.exceptions.ConnectionError:
            print(f"[Parser] OCR service unavailable: {api_url}")
            return None
        except Exception as error:
            print(f"[Parser] OCR request failed for {os.path.basename(image_path)}: {error}")
            return None


    @staticmethod
    def _has_meaningful_visual_content(image_bytes: bytes) -> bool:
        """Drop nearly empty white crops."""
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
            print(f"[Parser] Crop check failed: {error}")
            return False


    @staticmethod
    def _infer_asset_kind(crop_key: str) -> str:
        lowered = crop_key.lower()
        if "table_box" in lowered:
            return "table"
        if "chart_box" in lowered:
            return "chart"
        if "image_box" in lowered:
            return "image"
        if "formula_box" in lowered:
            return "formula"
        return "visual"


    @staticmethod
    def _extract_bbox_from_crop_key(crop_key: str) -> List[int]:
        match = re.search(r"_(\d+)_(\d+)_(\d+)_(\d+)\.[a-z0-9]+$", crop_key.lower())
        if not match:
            return []
        return [int(match.group(index)) for index in range(1, 5)]


    def _process_single_page(
        self,
        page_num: int,
        image_path: str,
        base_name: str,
        images_dir: str,
    ) -> List[Dict]:
        print(f"[Parser] OCR page {page_num}")
        self._resize_image_for_ocr(image_path)

        result = self._send_image_to_kaggle(image_path)
        if not result:
            print(f"[Parser] Skip page {page_num}")
            return []

        parsing_blocks = result.get("parsing_blocks", [])
        visual_crops = result.get("visual_base64_crops", {})

        for block in parsing_blocks:
            if "block_id" in block:
                block["block_id"] = f"p{page_num}_{block['block_id']}"

        saved_crop_paths: dict[str, dict] = {}
        for crop_key, base64_data in visual_crops.items():
            asset_kind = self._infer_asset_kind(crop_key)
            if asset_kind not in DISPLAY_ASSET_KINDS:
                continue

            image_bytes = base64.b64decode(base64_data)
            with Image.open(io.BytesIO(image_bytes)) as image:
                width, height = image.size

            if width < MIN_SAVED_IMAGE_WIDTH or height < MIN_SAVED_IMAGE_HEIGHT:
                continue

            # Skip oversized non-image crops such as answer tables.
            if (
                asset_kind in {"table", "chart", "visual"}
                and width > MAX_SAVED_IMAGE_WIDTH
                and height > MAX_SAVED_IMAGE_HEIGHT
            ):
                continue

            if not self._has_meaningful_visual_content(image_bytes):
                continue

            safe_key = crop_key.replace("/", "_").replace("\\", "_")
            image_filename = f"p{page_num}_{safe_key}.png"
            image_filepath = os.path.join(images_dir, image_filename)
            figure_id = f"p{page_num}_{crop_key}"

            with open(image_filepath, "wb") as file:
                file.write(image_bytes)

            saved_crop_paths[figure_id] = {
                "asset_id": figure_id,
                "asset_kind": asset_kind,
                "page_num": page_num,
                "bbox": self._extract_bbox_from_crop_key(crop_key),
                "width": width,
                "height": height,
                "abs_path": os.path.abspath(image_filepath),
                "web_url": f"/images/{base_name}/{image_filename}",
                "storage_key": f"images/{base_name}/{image_filename}",
            }

        page_questions = group_blocks_into_questions(parsing_blocks, saved_crop_paths)
        print(f"[Parser] Page {page_num} blocks={len(page_questions)}")
        return page_questions


    @staticmethod
    def _serialize_question(question, exam_id: str) -> dict:
        question_dict = question.model_dump()
        question_dict["topic_tags"] = [
            tag.value if hasattr(tag, "value") else str(tag)
            for tag in question.topic_tags
        ]
        question_dict["exam_id"] = exam_id
        return question_dict


    def process(self, file_path: str, push_to_mongo: bool = False) -> Optional[str]:
        if not os.path.exists(file_path):
            print(f"[Parser] File not found: {file_path}")
            return None

        extension = os.path.splitext(file_path)[1].lower()
        if extension not in config.ALLOWED_EXTENSIONS:
            print(f"[Parser] Unsupported file type: {extension}")
            return None

        base_name = os.path.splitext(os.path.basename(file_path))[0]
        images_dir = os.path.join(self.output_dir, "images", base_name)
        os.makedirs(images_dir, exist_ok=True)

        source_type = "pdf" if extension == ".pdf" else "image"
        image_paths = (
            split_pdf_to_images(file_path)
            if source_type == "pdf"
            else [os.path.abspath(file_path)]
        )
        print(f"[Parser] Source={source_type} pages={len(image_paths)}")

        started_at = time.time()
        all_grouped_questions: list[dict] = []
        page_results: dict[int, list[dict]] = {}

        with ThreadPoolExecutor(max_workers=OCR_CONCURRENCY) as executor:
            futures = {
                executor.submit(
                    self._process_single_page,
                    page_index + 1,
                    image_path,
                    base_name,
                    images_dir,
                ): page_index + 1
                for page_index, image_path in enumerate(image_paths)
            }

            for future in as_completed(futures):
                page_num = futures[future]
                try:
                    page_results[page_num] = future.result()
                except Exception as error:
                    print(f"[Parser] Page {page_num} failed: {error}")
                    page_results[page_num] = []

        for page_num in sorted(page_results):
            all_grouped_questions.extend(page_results[page_num])

        if not all_grouped_questions:
            print("[Parser] No questions found")
            return None

        print(
            f"[Parser] OCR blocks={len(all_grouped_questions)} "
            f"time={time.time() - started_at:.1f}s"
        )

        try:
            parser_output = self.structurer.structure_output(
                questions_list=all_grouped_questions,
                source_type=source_type,
            )
            self.parser_output = parser_output
            print(
                f"[Parser] Parsed subject={parser_output.subject} "
                f"questions={parser_output.total_questions}"
            )

            exam_dict = {
                "id": parser_output.id,
                "subject": parser_output.subject,
                "grade": parser_output.grade,
                "exam_type": parser_output.exam_type,
                "year": parser_output.year,
                "source": parser_output.source,
                "total_questions": parser_output.total_questions,
                "generated": parser_output.generated,
                "duration": parser_output.duration,
                "metadata": parser_output.metadata,
                "created_at": parser_output.created_at,
                "question_ids": [question.id for question in parser_output.questions],
            }
            exam_filepath = os.path.join(self.output_dir, f"{base_name}_exam.json")
            with open(exam_filepath, "w", encoding="utf-8") as file:
                json.dump(exam_dict, file, ensure_ascii=False, indent=2)

            question_docs = [
                self._serialize_question(question, parser_output.id)
                for question in parser_output.questions
            ]
            questions_filepath = os.path.join(self.output_dir, f"{base_name}_questions.json")
            with open(questions_filepath, "w", encoding="utf-8") as file:
                json.dump(question_docs, file, ensure_ascii=False, indent=2)

            combined_filepath = os.path.join(self.output_dir, f"{base_name}_parsed.json")
            with open(combined_filepath, "w", encoding="utf-8") as file:
                file.write(parser_output.model_dump_json(indent=2))

            print(f"[Parser] Saved {exam_filepath}")
            print(f"[Parser] Saved {questions_filepath}")
            print(f"[Parser] Saved {combined_filepath}")

            if push_to_mongo:
                if self.mongo_client.is_configured():
                    self.mongo_client.push_parser_output(parser_output)
                else:
                    print("[Mongo] Skip push")

            return combined_filepath
        except Exception as error:
            print(f"[Parser] Structuring failed: {error}")
            import traceback
            traceback.print_exc()
            return None
