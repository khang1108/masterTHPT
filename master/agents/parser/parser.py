from typing import Optional
from master.agents import BaseAgent
from master.agents.common.tools import ToolsRegistry
from master.agents.common.message import Intent, MessageRequest
from master.agents.common.state import AgentState
from master.agents.common.llm_client import LLMClient
from master.agents.common.prompt import parser_ocr_instruction
from PIL import Image
import fitz
import io
import re
import base64
import os
import asyncio
import httpx
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote

from langchain_core.messages import HumanMessage

# OCR config
MAX_OCR_WIDTH = 1240
MAX_OCR_HEIGHT = 1754
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}
DEFAULT_IMAGE_BUCKET_URL = os.getenv("PARSER_IMAGE_BUCKET_URL")
DEFAULT_PARSER_BATCH_SIZE = max(1, int(os.getenv("PARSER_BATCH_SIZE", "2")))
DEFAULT_IMAGE_UPLOAD_URL_TEMPLATE = os.getenv("PARSER_IMAGE_UPLOAD_URL_TEMPLATE")
DEFAULT_IMAGE_UPLOAD_METHOD = os.getenv("PARSER_IMAGE_UPLOAD_METHOD", "PUT")
DEFAULT_IMAGE_UPLOAD_TIMEOUT_SEC = max(3, int(os.getenv("PARSER_IMAGE_UPLOAD_TIMEOUT_SEC", "20")))


def _is_truthy(value: Optional[str]) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _get_parser_image_bucket_url() -> Optional[str]:
    # Read env at runtime to avoid stale value when .env is loaded after import time.
    value = os.getenv("PARSER_IMAGE_BUCKET_URL")
    if value and value.strip():
        return value.strip()
    if DEFAULT_IMAGE_BUCKET_URL and DEFAULT_IMAGE_BUCKET_URL.strip():
        return DEFAULT_IMAGE_BUCKET_URL.strip()
    return None


def _build_image_url(base_url: Optional[str], image_name: str) -> Optional[str]:
    if not base_url:
        return None

    root = base_url.strip()
    if not root:
        return None

    if "drive.google.com/drive/folders/" in root:
        # A Drive folder URL cannot directly resolve file-by-name without Drive API lookup.
        return root

    if "{image_name}" in root:
        return root.replace("{image_name}", quote(image_name))

    if "?" in root:
        joiner = "&" if not root.endswith(("?", "&")) else ""
        return f"{root}{joiner}file={image_name}"

    return f"{root.rstrip('/')}/{image_name}"


def _extract_response_url(response: httpx.Response, fallback_url: str) -> str:
    try:
        payload = response.json()
    except Exception:
        return fallback_url

    if isinstance(payload, dict):
        for key in ("url", "image_url", "public_url", "file_url"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

        data = payload.get("data")
        if isinstance(data, dict):
            for key in ("url", "image_url", "public_url", "file_url"):
                value = data.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()

    return fallback_url


def _extract_drive_folder_id(url: Optional[str]) -> Optional[str]:
    if not url:
        return None

    match = re.search(r"/folders/([a-zA-Z0-9_-]+)", url)
    if not match:
        return None
    return match.group(1)


class ParserAgent(ToolsRegistry, BaseAgent):

    def __init__(self):
        super().__init__(agent_role="Parser")
        self._ocr_llm = None
        self._trace_thread_id: Optional[str] = None

    async def setup(self):
        self.logger.agent_node("Parser setup started")
        self._ensure_ocr_llm()
        self.logger.agent_node("Parser setup completed")

    def _ensure_ocr_llm(self):
        if self._ocr_llm is None:
            self._ocr_llm = LLMClient.chat_model(
                provider="openai_compatible",
                base_url=os.getenv("FPT_BASE_URL"),
                api_key=os.getenv("FPT_API_KEY"),
                model=os.getenv("PARSER_OCR_MODEL", os.getenv("LLM_MODEL", "gemma-4-31B-it")),
                temperature=0.0,
            )
        return self._ocr_llm

    def _load_page_payloads(self, file_path: str) -> tuple[str, list[tuple[int, bytes, str]]]:
        ext = os.path.splitext(file_path)[1].lower()
        source_type = "pdf" if ext == ".pdf" else "image"
        base_name = os.path.splitext(os.path.basename(file_path))[0]

        if source_type == "pdf":
            zoom = 300 / 72.0
            matrix = fitz.Matrix(zoom, zoom)
            doc = fitz.open(file_path)
            payloads: list[tuple[int, bytes, str]] = []
            for page_num in range(doc.page_count):
                page = doc.load_page(page_num)
                pix = page.get_pixmap(matrix=matrix, alpha=False)
                payloads.append((
                    page_num + 1,
                    pix.tobytes("png"),
                    f"{base_name}_page_{page_num + 1:03d}.png",
                ))
            doc.close()
            return source_type, payloads

        with open(file_path, "rb") as f:
            raw_bytes = f.read()
        return source_type, [(1, raw_bytes, os.path.basename(file_path))]

    def _ocr_page(self, image_bytes: bytes, image_name: str) -> str:
        llm = self._ensure_ocr_llm()

        try:
            with Image.open(io.BytesIO(image_bytes)) as img:
                w, h = img.size
                if w > MAX_OCR_WIDTH or h > MAX_OCR_HEIGHT:
                    scale = min(MAX_OCR_WIDTH / w, MAX_OCR_HEIGHT / h)
                    img = img.convert("RGB").resize((int(w * scale), int(h * scale)), Image.LANCZOS)
                elif img.mode != "RGB":
                    img = img.convert("RGB")
                out = io.BytesIO()
                img.save(out, format="PNG", optimize=True)
                image_bytes = out.getvalue()
        except Exception:
            pass

        message = HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": parser_ocr_instruction(),
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{base64.b64encode(image_bytes).decode('utf-8')}"
                    },
                },
            ]
        )

        if self._trace_thread_id:
            response = llm.invoke(
                [message],
                config={"configurable": {"thread_id": self._trace_thread_id}},
            )
        else:
            response = llm.invoke([message])
        content = getattr(response, "content", "")
        if isinstance(content, str):
            text = content
        elif isinstance(content, list):
            chunks: list[str] = []
            for item in content:
                if isinstance(item, dict):
                    txt = item.get("text")
                    if txt:
                        chunks.append(str(txt))
                else:
                    chunks.append(str(item))
            text = "\n".join(chunks)
        else:
            text = str(content)

        text = re.sub(r"^```(?:text|markdown)?\s*", "", text.strip())
        text = re.sub(r"\s*```$", "", text).strip()
        if not text:
            raise RuntimeError(f"Qwen OCR tra ve rong cho {image_name}")
        return text

    def _upload_page_image(
        self,
        image_bytes: bytes,
        image_name: str,
        image_bucket_url: Optional[str],
    ) -> Optional[str]:
        upload_template = os.getenv("PARSER_IMAGE_UPLOAD_URL_TEMPLATE")
        if not upload_template:
            upload_template = DEFAULT_IMAGE_UPLOAD_URL_TEMPLATE
        if not upload_template and image_bucket_url and "{image_name}" in image_bucket_url:
            upload_template = image_bucket_url

        upload_enabled = _is_truthy(os.getenv("PARSER_IMAGE_UPLOAD_ENABLED", "true"))
        if upload_template and not upload_enabled:
            self.logger.warning(
                "Parser image upload template is configured but PARSER_IMAGE_UPLOAD_ENABLED=false; skipping upload"
            )
            return None

        # Upload strategy 1: explicit HTTP upload template.
        if upload_template:
            upload_url = upload_template.replace("{image_name}", quote(image_name))
            method = os.getenv("PARSER_IMAGE_UPLOAD_METHOD", DEFAULT_IMAGE_UPLOAD_METHOD).upper().strip() or "PUT"

            timeout_raw = os.getenv("PARSER_IMAGE_UPLOAD_TIMEOUT_SEC", str(DEFAULT_IMAGE_UPLOAD_TIMEOUT_SEC))
            try:
                timeout_sec = max(3, int(timeout_raw))
            except Exception:
                timeout_sec = DEFAULT_IMAGE_UPLOAD_TIMEOUT_SEC

            headers = {
                "Content-Type": "image/png",
                "X-File-Name": image_name,
            }

            bearer = os.getenv("PARSER_IMAGE_UPLOAD_BEARER_TOKEN")
            if bearer and bearer.strip():
                headers["Authorization"] = f"Bearer {bearer.strip()}"

            api_key = os.getenv("PARSER_IMAGE_UPLOAD_API_KEY")
            if api_key and api_key.strip():
                headers["x-api-key"] = api_key.strip()

            try:
                response = httpx.request(
                    method,
                    upload_url,
                    content=image_bytes,
                    headers=headers,
                    timeout=timeout_sec,
                )
                response.raise_for_status()
                return _extract_response_url(response, upload_url)
            except Exception as e:
                self.logger.warning(f"Parser image upload failed image={image_name}: {e}")
                return None

        # Upload strategy 2: Google Drive folder URL + access token.
        drive_folder_id = _extract_drive_folder_id(image_bucket_url)
        drive_access_token = os.getenv("GOOGLE_DRIVE_ACCESS_TOKEN")
        if drive_folder_id and drive_access_token and drive_access_token.strip():
            timeout_raw = os.getenv("PARSER_IMAGE_UPLOAD_TIMEOUT_SEC", str(DEFAULT_IMAGE_UPLOAD_TIMEOUT_SEC))
            try:
                timeout_sec = max(3, int(timeout_raw))
            except Exception:
                timeout_sec = DEFAULT_IMAGE_UPLOAD_TIMEOUT_SEC

            metadata = {
                "name": image_name,
                "parents": [drive_folder_id],
                "mimeType": "image/png",
            }

            multipart_files = {
                "metadata": (None, json.dumps(metadata), "application/json; charset=UTF-8"),
                "file": (image_name, image_bytes, "image/png"),
            }
            headers = {"Authorization": f"Bearer {drive_access_token.strip()}"}

            try:
                upload_response = httpx.post(
                    "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&supportsAllDrives=true",
                    files=multipart_files,
                    headers=headers,
                    timeout=timeout_sec,
                )
                upload_response.raise_for_status()
                uploaded = upload_response.json()
                file_id = uploaded.get("id")
                if not file_id:
                    return None

                # Try making file public; if permission call fails we still return Drive URL.
                try:
                    permission_response = httpx.post(
                        f"https://www.googleapis.com/drive/v3/files/{file_id}/permissions?supportsAllDrives=true",
                        headers={
                            "Authorization": f"Bearer {drive_access_token.strip()}",
                            "Content-Type": "application/json",
                        },
                        json={"role": "reader", "type": "anyone"},
                        timeout=timeout_sec,
                    )
                    permission_response.raise_for_status()
                except Exception as perm_err:
                    self.logger.warning(
                        f"Parser uploaded to Drive but failed to set public permission image={image_name}: {perm_err}"
                    )

                return f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"
            except Exception as e:
                self.logger.warning(f"Parser Drive upload failed image={image_name}: {e}")
                return None

        if drive_folder_id and not drive_access_token:
            self.logger.warning(
                "Parser image upload skipped for Google Drive because GOOGLE_DRIVE_ACCESS_TOKEN is not set"
            )

        return None

    def ocr_to_text(self, file_path: str, batch_size: Optional[int] = None) -> Optional[str]:
        if not os.path.exists(file_path):
            self.logger.warning(f"Parser input file not found: {file_path}")
            return None

        ext = os.path.splitext(file_path)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            self.logger.warning(f"Parser input extension not supported: {ext}")
            return None

        source_type = "pdf" if ext == ".pdf" else "image"
        self.logger.agent_node(
            f"Parser OCR source={source_type} file={os.path.basename(file_path)}"
        )

        image_bucket_url = _get_parser_image_bucket_url()
        _, page_payloads = self._load_page_payloads(file_path)
        page_name_by_num = {page_num: image_name for page_num, _, image_name in page_payloads}

        effective_batch_size = max(1, int(batch_size or DEFAULT_PARSER_BATCH_SIZE))
        total_pages = len(page_payloads)
        total_batches = (total_pages + effective_batch_size - 1) // effective_batch_size
        self.logger.agent_node(
            f"Parser OCR batching configured batch_size={effective_batch_size} total_pages={total_pages}"
        )

        page_image_urls: dict[int, str] = {}
        uploaded_pages = 0
        if image_bucket_url and total_pages > 0:
            upload_workers = min(4, total_pages)
            with ThreadPoolExecutor(max_workers=upload_workers) as upload_executor:
                upload_futures = {
                    upload_executor.submit(
                        self._upload_page_image,
                        image_bytes,
                        image_name,
                        image_bucket_url,
                    ): (page_num, image_name)
                    for page_num, image_bytes, image_name in page_payloads
                }

                for future in as_completed(upload_futures):
                    page_num, image_name = upload_futures[future]
                    uploaded_url: Optional[str] = None
                    try:
                        uploaded_url = future.result()
                    except Exception as e:
                        self.logger.warning(f"Parser image upload task failed page={page_num}: {e}")

                    final_url = uploaded_url or _build_image_url(image_bucket_url, image_name)
                    if final_url:
                        page_image_urls[page_num] = final_url
                    if uploaded_url:
                        uploaded_pages += 1

            self.logger.agent_node(
                "Parser image URL resolution completed "
                f"uploaded={uploaded_pages}/{total_pages} resolved={len(page_image_urls)}/{total_pages}"
            )

        pages_text: list[str] = []
        completed_pages = 0
        for batch_start in range(0, total_pages, effective_batch_size):
            batch = page_payloads[batch_start: batch_start + effective_batch_size]
            batch_index = (batch_start // effective_batch_size) + 1
            batch_page_nums = [p[0] for p in batch]
            self.logger.agent_node(
                f"Parser OCR batch {batch_index}/{total_batches} started pages={batch_page_nums}"
            )

            batch_results: dict[int, str] = {}
            with ThreadPoolExecutor(max_workers=effective_batch_size) as executor:
                future_map = {
                    executor.submit(self._ocr_page, image_bytes, image_name): page_num
                    for page_num, image_bytes, image_name in batch
                }

                for future in as_completed(future_map):
                    page_num = future_map[future]
                    try:
                        page_text = future.result()
                        if page_text:
                            batch_results[page_num] = page_text
                        completed_pages += 1
                        self.logger.agent_node(
                            f"Parser OCR page done page={page_num} progress={completed_pages}/{total_pages}"
                        )
                    except Exception as e:
                        completed_pages += 1
                        self.logger.warning(f"Parser OCR failed page={page_num}: {e}")
                        self.logger.agent_node(
                            f"Parser OCR page failed page={page_num} progress={completed_pages}/{total_pages}"
                        )

            for page_num, _, _ in batch:
                page_text = batch_results.get(page_num)
                if page_text:
                    image_name = page_name_by_num.get(page_num, "")
                    image_url = page_image_urls.get(page_num)
                    if not image_url and image_name:
                        image_url = _build_image_url(image_bucket_url, image_name)
                    page_header = f"=== PAGE {page_num} ==="
                    if image_url:
                        page_header = f"{page_header}\nIMAGE_URL: {image_url}"
                    pages_text.append(f"{page_header}\n{page_text}")

            self.logger.agent_node(
                f"Parser OCR batch {batch_index}/{total_batches} completed success={len(batch_results)}/{len(batch)}"
            )

        if not pages_text:
            self.logger.warning("Parser OCR produced empty output")
            return None

        parser_output = "\n\n".join(pages_text)
        return parser_output

    @staticmethod
    def build_preprocess_request(
        parser_output: str,
        student_id: str,
        exam_id: Optional[str] = None,
        image_bucket_url: Optional[str] = None,
    ) -> MessageRequest:
        return MessageRequest(
            intent=Intent.PREPROCESS,
            student_id=student_id,
            exam_id=exam_id,
            parser_output=parser_output,
            image_bucket_url=image_bucket_url or _get_parser_image_bucket_url(),
        )

    @staticmethod
    def build_agent_state(request: MessageRequest) -> AgentState:
        return AgentState(
            request=request,
            learner_profile=None,
            exam_id=request.exam_id,
            questions=[],
            student_answers=request.student_answers or [],
            raw_request=request,
            round=0,
            max_round=0,
            phase="finalize",
            debate_outputs=[],
            grade_result=None,
            solutions=None,
            verified_solutions=None,
            selected_questions=None,
            profile_updates=None,
            response=None,
        )

    async def process(
        self,
        file_path: str,
        student_id: str = "parser",
        exam_id: Optional[str] = None,
        batch_size: Optional[int] = None,
        thread_id: Optional[str] = None,
    ) -> Optional[MessageRequest]:
        effective_batch_size = max(1, int(batch_size or DEFAULT_PARSER_BATCH_SIZE))
        self.logger.agent_node(
            f"Parser process started file_path={file_path} batch_size={effective_batch_size}"
        )
        self._trace_thread_id = thread_id
        try:
            parser_output = self.ocr_to_text(file_path, batch_size=effective_batch_size)
        finally:
            self._trace_thread_id = None
        if not parser_output:
            self.logger.agent_node("Parser process completed with empty parser_output")
            return None

        request = self.build_preprocess_request(
            parser_output=parser_output,
            student_id=student_id,
            exam_id=exam_id,
            image_bucket_url=_get_parser_image_bucket_url(),
        )
        self.logger.agent_node(
            f"Parser process completed parser_output_len={len(parser_output)}"
        )
        return request

    async def process_to_state(
        self,
        file_path: str,
        student_id: str = "parser",
        exam_id: Optional[str] = None,
        batch_size: Optional[int] = None,
        thread_id: Optional[str] = None,
    ) -> Optional[AgentState]:
        request = await self.process(
            file_path=file_path,
            student_id=student_id,
            exam_id=exam_id,
            batch_size=batch_size,
            thread_id=thread_id,
        )
        if request is None:
            return None
        return self.build_agent_state(request)

    async def run(self, input: str) -> str:
        """BaseAgent interface: nhận đường dẫn file và trả OCR text."""
        self.logger.agent_node(
            f"Parser run started input={input} batch_size={DEFAULT_PARSER_BATCH_SIZE}"
        )
        result = self.ocr_to_text(input, batch_size=DEFAULT_PARSER_BATCH_SIZE)
        self.logger.agent_node(
            f"Parser run completed parser_output_len={len(result) if result else 0}"
        )
        return result or ""


def process_sync(
    file_path: str,
    student_id: str = "parser",
    exam_id: Optional[str] = None,
    batch_size: Optional[int] = None,
    thread_id: Optional[str] = None,
) -> Optional[MessageRequest]:
    parser = ParserAgent()
    return asyncio.run(
        parser.process(
            file_path=file_path,
            student_id=student_id,
            exam_id=exam_id,
            batch_size=batch_size,
            thread_id=thread_id,
        )
    )
