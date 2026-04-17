"""Deterministic helpers for extracting a knowledge graph from textbook markdown."""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterable, Sequence

if TYPE_CHECKING:
    from langchain_core.language_models.chat_models import BaseChatModel
    from .model import ExtractionDocument


_IMAGE_RE = re.compile(r"!\[[^\]]*\]\([^)]+\)")
_BLANK_LINES_RE = re.compile(r"\n{3,}")
_ANY_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_GRADE_RE = re.compile(r"toan-(10|11|12)-tap-(1|2)")
_STOP_HEADINGS = (
    "HUONG DAN SU DUNG SACH",
    "LOI NOI DAU",
    "MUC LUC",
    "HOI DONG",
    "CHUONG ",
    "BAI TAP",
    "BAI TAP CUOI CHUONG",
    "VI DU",
    "LUYEN TAP",
    "GIAI",
    "A - TRAC NGHIEM",
    "A – TRAC NGHIEM",
    "B - TU LUAN",
    "B – TU LUAN",
    "VOI CUOC SONG",
    "EM CO BIET",
    "THUAT NGU",
    "MUC TIEU",
    "KIEN THUC",
    "KIEN THUC, KI NANG",
    "BANG TRA CUU",
    "CHIU TRACH NHIEM",
    "BAN QUYEN",
    "CAC DON VI DAU MOI PHAT HANH",
    "NHA XUAT BAN GIAO DUC VIET NAM XIN",
    "GOI Y THUC HIEN",
    "VAN DUNG",
    "TOAN 12 TAP",
    "TOAN 11 TAP",
    "VE DO HOA",
    "PENROSE",
    "MOBIUS",
)


@dataclass(frozen=True)
class ExtractionConfig:
    """Tunable controls for chunking and extraction orchestration."""

    min_body_chars: int = 180
    max_chunk_chars: int = 6000
    keep_exercise_sections: bool = False


@dataclass(frozen=True)
class MarkdownChunk:
    """Structured metadata and content for one extractable section of a textbook markdown file.

    Parameters:
    - chunk_id: A stable identifier for this chunk, e.g. "toan-11-tap-1:0001"
    - book_id: The canonical book identifier, e.g. "toan-11-tap-1"
    - grade: The inferred school grade, e.g. 11
    - source_path: The original markdown file path for traceability
    - order: The sequential order of this chunk within the book, starting at 1
    - title: The original heading text for this chunk, e.g. "Hình học không gian"
    - content: The cleaned markdown body text for this chunk, ready for LLM input
    - chapter_title: The current chapter title if applicable, e.g. "Chương 3: Hình học không gian", otherwise None
    """

    chunk_id: str
    book_id: str
    grade: int | None
    source_path: str
    order: int
    title: str
    content: str
    chapter_title: str | None = None

    @property
    def combined_text(self) -> str:
        """Render metadata plus content into a single extraction payload."""

        chapter_line = f"Chapter: {self.chapter_title}\n" if self.chapter_title else ""
        return (
            f"Chunk ID: {self.chunk_id}\n"
            f"Book ID: {self.book_id}\n"
            f"Grade: {self.grade}\n"
            f"{chapter_line}"
            f"Title: {self.title}\n\n"
            f"{self.content}"
        )


def list_markdown_files(base_dir: str | Path) -> list[Path]:
    """Return textbook markdown files in deterministic order."""

    base_path = Path(base_dir)
    return sorted(base_path.glob("sach-giao-khoa-toan-*-ket-noi-tri-thuc-voi-cuoc-song.md"))


def build_chat_model(
    *,
    provider: str | None = None,
    model: str | None = None,
    temperature: float = 0.1,
    max_tokens: int = 4096,
) -> "BaseChatModel":
    """Create a low-temperature chat model suitable for structured extraction."""

    from master.agents.common.llm_client import LLMClient

    return LLMClient.chat_model(
        provider=provider,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )


def clean_markdown_text(raw_text: str) -> str:
    """Remove noisy OCR/image artifacts while preserving math-heavy content."""

    text = _IMAGE_RE.sub("", raw_text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _BLANK_LINES_RE.sub("\n\n", text)
    return text.strip()


def normalize_heading(heading: str) -> str:
    """Normalize headings for filtering without changing the original source text."""

    collapsed = re.sub(r"[*_`#>\-]+", " ", heading)
    collapsed = re.sub(r"\s+", " ", collapsed).strip()
    collapsed = collapsed.replace("Đ", "D").replace("đ", "d")
    ascii_only = unicodedata.normalize("NFD", collapsed)
    ascii_only = "".join(char for char in ascii_only if not unicodedata.combining(char))
    ascii_only = re.sub(r"\s+", " ", ascii_only).strip()
    return ascii_only.upper()


def infer_book_id(source_path: str | Path) -> str:
    """Build a stable book identifier from the markdown filename."""

    path = Path(source_path)
    stem = path.stem.lower()
    stem = stem.replace("sach-giao-khoa-", "")
    stem = stem.replace("-ket-noi-tri-thuc-voi-cuoc-song", "")
    return stem


def infer_grade_from_book_id(book_id: str) -> int | None:
    """Extract the school grade from the canonical book identifier."""

    match = _GRADE_RE.search(book_id)
    if not match:
        return None
    return int(match.group(1))


def should_skip_heading(heading: str, *, keep_exercise_sections: bool = False) -> bool:
    """Heuristic filter for front matter and non-knowledge sections."""

    raw = heading.strip()
    if "$" in raw:
        return True
    if raw.startswith(">"):
        return True
    if re.match(r"^H\d+", raw):
        return True
    if re.match(r"^[a-z]\)", raw):
        return True
    if raw.startswith(")"):
        return True

    normalized = normalize_heading(heading)
    compact = normalized.replace(" ", "")
    if "HD" in compact[:6]:
        return True
    alpha_count = sum(char.isalpha() for char in normalized)
    if alpha_count < 5:
        return True
    if keep_exercise_sections and compact.startswith("BAITAP"):
        return False
    for marker in _STOP_HEADINGS:
        normalized_marker = normalize_heading(marker)
        compact_marker = normalized_marker.replace(" ", "")
        if normalized_marker in normalized or compact_marker in compact:
            return True
    return False


def trim_chunk_body(body: str, max_chars: int) -> str:
    """Limit chunk size without cutting mid-sentence too aggressively."""

    if len(body) <= max_chars:
        return body

    shortened = body[:max_chars]
    last_break = max(shortened.rfind("\n\n"), shortened.rfind(". "))
    if last_break >= max_chars // 2:
        return shortened[:last_break].strip()
    return shortened.strip()


def chunk_markdown_file(
    source_path: str | Path,
    *,
    config: ExtractionConfig | None = None,
) -> list[MarkdownChunk]:
    """Split one textbook markdown file into extractable H1 sections."""

    cfg = config or ExtractionConfig()
    path = Path(source_path)
    text = clean_markdown_text(path.read_text(encoding="utf-8"))
    chunks: list[MarkdownChunk] = []
    book_id = infer_book_id(path)
    grade = infer_grade_from_book_id(book_id)
    current_chapter: str | None = None

    current_heading: str | None = None
    current_body: list[str] = []

    def flush_current_chunk() -> None:
        nonlocal current_heading, current_body
        if not current_heading:
            return

        body = "\n".join(current_body).strip()
        if should_skip_heading(
            current_heading,
            keep_exercise_sections=cfg.keep_exercise_sections,
        ):
            current_heading = None
            current_body = []
            return

        if len(body) < cfg.min_body_chars:
            current_heading = None
            current_body = []
            return

        trimmed_body = trim_chunk_body(body, cfg.max_chunk_chars)
        chunk_id = f"{book_id}:{len(chunks) + 1:04d}"
        chunks.append(
            MarkdownChunk(
                chunk_id=chunk_id,
                book_id=book_id,
                grade=grade,
                source_path=str(path),
                order=len(chunks) + 1,
                title=current_heading,
                content=trimmed_body,
                chapter_title=current_chapter,
            )
        )
        current_heading = None
        current_body = []

    for line in text.splitlines():
        match = _ANY_HEADING_RE.match(line)
        if not match:
            if current_heading is not None:
                current_body.append(line)
            continue

        level = len(match.group(1))
        heading = match.group(2).strip()
        normalized = normalize_heading(heading)

        if normalized.startswith("CHUONG ") and level <= 2:
            flush_current_chunk()
            current_chapter = heading
            continue

        if level <= 2:
            flush_current_chunk()
            current_heading = heading
            current_body = []
            continue

        if current_heading is not None:
            current_body.append(line)

    flush_current_chunk()

    return chunks


def chunk_markdown_corpus(
    file_paths: Sequence[str | Path],
    *,
    config: ExtractionConfig | None = None,
) -> list[MarkdownChunk]:
    """Chunk every textbook file and flatten the result into one sequence."""

    all_chunks: list[MarkdownChunk] = []
    for path in file_paths:
        all_chunks.extend(chunk_markdown_file(path, config=config))
    return all_chunks


def build_extraction_messages(chunk: MarkdownChunk) -> list[Any]:
    """Generate a strict extraction prompt for one textbook chunk."""

    from langchain_core.messages import HumanMessage, SystemMessage

    payload = build_extraction_message_payload(chunk)
    return [
        SystemMessage(content=payload[0]["content"]),
        HumanMessage(content=payload[1]["content"]),
    ]


def build_extraction_message_payload(chunk: MarkdownChunk) -> list[dict[str, str]]:
    """Generate provider-agnostic chat payload messages for one chunk."""

    system_prompt = (
        "Bạn là một Giáo viên Toán học Trung học Phổ thông tại Việt Nam và là một Kỹ sư Thiết kế Đồ thị Tri thức xuất sắc."
        "Nhiệm vụ của bạn là đọc các đoạn văn bản Markdown được trích xuất từ Sách giáo khoa Toán (đã giữ nguyên công thức LaTeX) và phân rã chúng thành các Khái niệm Hạt nhân."
        "Khái niệm hạt nhân là đơn vị kiến thức nhỏ nhất, đủ để có thể tạo ra một câu hỏi đơn giản nhất có thể. Ví dụ 'Định lý Pytagores', 'Định lý Cosin', ..."
        "# Yêu cầu trích xuất:"
        "- Chuẩn hóa Định danh: Mọi khái niệm được trích ra (Node) phải có một id duy nhất, định dạng chữ in hoa, không dấu, ngăn cách bằng dấu gạch dưới, và bắt đầu bằng tiền tố C_ (ví dụ: C_HAM_SO_BAC_HAI, C_CONG_THUC_HERON)."
        "- Giới hạn Loại Khái niệm (Node Types): Các khái niệm chỉ được phép rơi vào một trong 3 loại: CONCEPT (Lý thuyết chung), THEOREM (Định lý), hoặc FORMULA (Công thức)."
        "- Hướng của Cạnh (Edge Directionality): Khi thiết lập mối quan hệ giữa hai Node, bạn chỉ được phép sử dụng các nhãn:"
        "  `REQUIRES`: Khái niệm A là tiên quyết, BẮT BUỘC phải học trước khi học khái niệm B. (Ví dụ: Định lý Pythagoras REQUIRES Tam giác vuông)."
        "  `PART_OF`: Khái niệm A là một thành phần nhỏ phụ thuộc trực tiếp vào khái niệm B."
        "  `RELATED_TO`: Có liên quan về mặt toán học nhưng không ràng buộc tính tuần tự trước/sau."
        "  Bảo tồn LaTeX (LaTeX Binding): TUYỆT ĐỐI giữ nguyên mọi biểu thức toán học bao quanh bởi dấu $ hoặc $$. Không được phép diễn giải chúng thành văn bản thông thường."
        "  Chống Ảo giác (Anti-Hallucination): Chỉ trích xuất các Node và Edge được thể hiện rõ ràng hoặc suy luận logic trực tiếp từ đoạn văn bản đầu vào. Nếu đoạn văn bản không chứa mối quan hệ, tuyệt đối không bịa đặt, hãy để danh sách Edges trống."
        "\n\n"
    )
    user_prompt = (
        "Trích xuất kiến thức từ đoạn văn sau thành các Khái niệm Hạt nhân.  \n\n"
        f"{chunk.combined_text}"
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def extract_graph_for_chunk(
    chunk: MarkdownChunk,
    *,
    llm: "BaseChatModel",
) -> "ExtractionDocument":
    """Run one structured LLM extraction for a single chunk."""

    from .model import ExtractionDocument

    structured_llm = llm.with_structured_output(ExtractionDocument)
    document = structured_llm.invoke(build_extraction_messages(chunk))
    if not document.chunk_id:
        document.chunk_id = chunk.chunk_id
    return document


def merge_graph_documents(documents: Iterable["ExtractionDocument"]) -> "ExtractionDocument":
    """Deduplicate nodes and edges from many chunk-level extraction results."""

    from .model import ExtractionDocument, KnowledgeEdge, KnowledgeNode

    node_map: dict[str, KnowledgeNode] = {}
    edge_map: dict[tuple[str, str, str], KnowledgeEdge] = {}
    summaries: list[str] = []

    for document in documents:
        summaries.append(f"{document.chunk_id}: {document.summary}")
        for node in document.nodes:
            node_map.setdefault(node.id, node)
        for edge in document.edges:
            key = (edge.source, edge.relation, edge.target)
            edge_map.setdefault(key, edge)

    return ExtractionDocument(
        chunk_id="merged-corpus",
        summary="\n".join(summaries),
        nodes=sorted(node_map.values(), key=lambda item: item.id),
        edges=sorted(
            edge_map.values(),
            key=lambda item: (item.source, item.relation, item.target),
        ),
    )


def extract_corpus_graph(
    chunks: Sequence[MarkdownChunk],
    *,
    llm: "BaseChatModel",
    limit: int | None = None,
) -> tuple[list["ExtractionDocument"], "ExtractionDocument"]:
    """Extract chunk-level graphs and return both raw and merged results."""

    selected_chunks = list(chunks[:limit] if limit is not None else chunks)
    documents = [extract_graph_for_chunk(chunk, llm=llm) for chunk in selected_chunks]
    merged = merge_graph_documents(documents)
    return documents, merged


def export_graph_json(document: Any, destination: str | Path) -> Path:
    """Persist one extraction document as pretty JSON."""

    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(document.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path
