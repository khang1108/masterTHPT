# PDF → Skill Set (SGK presentation) — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a repeatable pipeline that ingests **SGK PDFs** (Toán 10–12), recovers **structure theo cách sách trình bày** (phần → chương → bài/mục), extracts **atomic skill candidates**, then **canonicalizes** them to **CTGDPT-anchored** `skill_id`s and emits versioned **YAML/JSON** ready for the knowledge graph and question tagging.

**Architecture:** PDFs are **evidence** and **layout/lexical source**, not the authority for identifiers. **Chương trình GDPT 2018** remains the **source of truth** for stable `skill_id`s (see [docs/superpowers/specs/2026-04-12-master-architecture-redesign.md](docs/superpowers/specs/2026-04-12-master-architecture-redesign.md) §4.4). The pipeline: (1) ingest + normalize PDF, (2) extract text per page with provenance, (3) detect SGK headings (rule-based + optional LLM assist), (4) chunk into **lesson-level** segments, (5) propose skill rows (title, summary, cognitive level optional via NHSGE tags already stubbed in [master/agents/adaptive/skill/build_skill.py](master/agents/adaptive/skill/build_skill.py)), (6) **align** each candidate to existing CT skill table or mark `needs_review`, (7) validate + export `math_ct_skills.yaml` / draft files, (8) optional merge into [docs/superpowers/plans/2026-04-14-sgk-math-knowledge-graph.md](docs/superpowers/plans/2026-04-14-sgk-math-knowledge-graph.md) graph tasks.

**Tech Stack:** Python 3.11+; `pymupdf` (fitz) or `pypdf` for text; `pdfplumber` optional for tables; **VLM/LLM** only for structuring/alignment steps (bounded JSON schema); Pydantic for schemas; output YAML under `data/knowledge_graph/`. Neo4j/Node import is **out of scope** for this document—reuse Task 5 of the KG plan after YAML exists.

**Related spec:** §4.4 CT anchoring; edge types PREREQUISITE / RELATED / EXTENDS_ACROSS_GRADE.

---

## Chunk 1: Repository layout and schemas

### Task 1: Directory layout and README

**Files:**
- Create: `data/knowledge_graph/README.md`
- Create: `data/knowledge_graph/_schema/skill_record.schema.json`
- Create: `master/skill_pipeline/README.md`

- [ ] **Step 1: Create `data/knowledge_graph/README.md`** explaining: (a) CT is authoritative for `skill_id`; (b) SGK PDF pipeline produces `draft/` YAML for review; (c) `math_ct_skills.yaml` is merged only after human sign-off.

- [ ] **Step 2: Define JSON Schema for one skill record** (used to validate YAML before merge). Minimal fields:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://master.local/schemas/skill_record.schema.json",
  "type": "object",
  "required": ["skill_id", "grade", "domain", "title_vi"],
  "properties": {
    "skill_id": { "type": "string", "pattern": "^math\\.g(10|11|12)\\.[a-z0-9_]+(\\.[a-z0-9_]+)*$" },
    "grade": { "type": "integer", "enum": [10, 11, 12] },
    "domain": { "type": "string", "minLength": 1 },
    "title_vi": { "type": "string", "minLength": 1 },
    "chapter_label": { "type": "string" },
    "ct_anchor": { "type": "string", "description": "Quote or code reference to CTGDPT text" },
    "aliases": { "type": "array", "items": { "type": "string" } },
    "sgk_refs": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["publisher", "grade", "path"],
        "properties": {
          "publisher": { "type": "string" },
          "grade": { "type": "integer" },
          "path": { "type": "string", "description": "e.g. Phần I > Chương 2 > Bài 3" }
        }
      }
    },
    "nhsge_level": { "type": "string", "enum": ["NB", "TH", "VD", "VDC"] },
    "provenance": {
      "type": "object",
      "properties": {
        "source_pdf_sha256": { "type": "string" },
        "page_range": { "type": "string" }
      }
    },
    "status": { "type": "string", "enum": ["draft", "aligned", "approved"] }
  },
  "additionalProperties": true
}
```

- [ ] **Step 3: Commit**

```bash
git add data/knowledge_graph/README.md data/knowledge_graph/_schema/skill_record.schema.json master/skill_pipeline/README.md
git commit -m "docs: add skill_record schema and KG data README for PDF pipeline"
```

---

## Chunk 2: PDF ingest and text extraction

### Task 2: Ingest CLI — copy/hash/metadata

**Files:**
- Create: `master/skill_pipeline/ingest_pdf.py`
- Create: `tests/test_ingest_pdf.py`

- [ ] **Step 1: Write failing test** — `tests/test_ingest_pdf.py`:

```python
import hashlib
from pathlib import Path
import tempfile

from master.skill_pipeline.ingest_pdf import ingest_pdf


def test_ingest_computes_sha256():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "sample.pdf"
        p.write_bytes(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        meta = ingest_pdf(p)
        assert meta.sha256 == hashlib.sha256(p.read_bytes()).hexdigest()
        assert meta.stem == "sample"
```

- [ ] **Step 2: Run test — expect FAIL** (module missing)

```bash
cd /home/phuckhang/MyWorkspace/GDGoC_HackathonVietnam
pytest tests/test_ingest_pdf.py::test_ingest_computes_sha256 -v
```

Expected: `ModuleNotFoundError` or import error.

- [ ] **Step 3: Add package init and minimal implementation**

Create `master/skill_pipeline/__init__.py` (empty).

Create `master/skill_pipeline/ingest_pdf.py`:

```python
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class IngestMeta:
    path: Path
    stem: str
    sha256: str
    byte_size: int


def ingest_pdf(pdf_path: Path) -> IngestMeta:
    pdf_path = pdf_path.resolve()
    data = pdf_path.read_bytes()
    return IngestMeta(
        path=pdf_path,
        stem=pdf_path.stem,
        sha256=hashlib.sha256(data).hexdigest(),
        byte_size=len(data),
    )
```

**Import path:** place implementation at `master/skill_pipeline/ingest_pdf.py` and test at `tests/test_ingest_pdf.py` with `from master.skill_pipeline.ingest_pdf import ingest_pdf` after ensuring repo root is on `PYTHONPATH`. If pytest cannot import, use:

```python
# tests/conftest.py
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
```

**Lock:** use `master/skill_pipeline/` as the Python package path to match existing `master/` layout.

- [ ] **Step 4: Run test — expect PASS**

```bash
pytest tests/test_ingest_pdf.py::test_ingest_computes_sha256 -v
```

- [ ] **Step 5: Commit**

```bash
git add master/skill_pipeline/ tests/test_ingest_pdf.py tests/conftest.py
git commit -m "feat(skill-pipeline): ingest_pdf metadata and sha256"
```

### Task 3: Extract text per page (native PDF)

**Files:**
- Create: `master/skill_pipeline/extract_pdf_text.py`
- Modify: `requirements.txt` (add `pymupdf`)

- [ ] **Step 1: Add dependency**

Add line to `requirements.txt`:

```
pymupdf>=1.24.0
```

Run:

```bash
pip install pymupdf
```

- [ ] **Step 2: Implement extraction**

`master/skill_pipeline/extract_pdf_text.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import fitz  # pymupdf


@dataclass
class PageText:
    page_index: int
    text: str


def extract_pages(pdf_path: Path) -> list[PageText]:
    doc = fitz.open(pdf_path)
    out: list[PageText] = []
    for i in range(doc.page_count):
        page = doc.load_page(i)
        out.append(PageText(page_index=i, text=page.get_text("text") or ""))
    doc.close()
    return out
```

- [ ] **Step 3: Test with a tiny real PDF** (commit a **small** fixture under `tests/fixtures/minimal.pdf` only if license permits; otherwise skip integration test and mock `fitz.open` — YAGNI: use one-page PDF generated in test via fitz if needed)

Minimal programmatic PDF in test:

```python
def test_extract_pages_roundtrip(tmp_path):
    import fitz
    p = tmp_path / "one.pdf"
    doc = fitz.open()
    doc.new_page()
    doc[0].insert_text((72, 72), "Chuong 1 Bai 1")
    doc.save(p)
    doc.close()
    from master.skill_pipeline.extract_pdf_text import extract_pages
    pages = extract_pages(p)
    assert len(pages) == 1
    assert "Chuong" in pages[0].text
```

- [ ] **Step 4: Commit**

```bash
git add master/skill_pipeline/extract_pdf_text.py requirements.txt tests/test_extract_pdf_text.py
git commit -m "feat(skill-pipeline): extract per-page text with pymupdf"
```

---

## Chunk 3: Detect SGK structure (presentation layer)

### Task 4: Heading heuristics for Vietnamese SGK

**Files:**
- Create: `master/skill_pipeline/sgk_structure.py`
- Create: `tests/test_sgk_structure.py`

**Idea:** SGK thường dùng các dòng in hoa / “Chương”, “Bài”, “Mục”, “Phần”. Bước 1 không cần LLM — regex + line scoring.

- [ ] **Step 1: Implement `segment_by_headings(pages: list[PageText]) -> list[Segment]`** where `Segment` has `title`, `level` (1=Phần, 2=Chương, 3=Bài), `page_start`, `page_end`, `body`.

Example patterns (tune against one real SGK PDF):

```python
import re

CHAPTER = re.compile(r"^\s*(CHƯƠNG|Chương)\s+(\d+|[IVXLCDM]+)\b", re.IGNORECASE)
LESSON = re.compile(r"^\s*(BÀI|Bài)\s+(\d+)\b", re.IGNORECASE)
PART = re.compile(r"^\s*(PHẦN|Phần)\s+([IVXLCDM]+|\d+)\b", re.IGNORECASE)
```

- [ ] **Step 2: Unit tests** with synthetic multi-line strings containing “Phần I”, “Chương 1”, “Bài 2”.

- [ ] **Step 3: Commit**

```bash
git add master/skill_pipeline/sgk_structure.py tests/test_sgk_structure.py
git commit -m "feat(skill-pipeline): segment SGK-like headings from page text"
```

### Task 5 (optional): Scanned PDF / poor text

**Files:**
- Document only in `master/skill_pipeline/README.md` (no code until needed)

- [ ] If `get_text` returns empty for >50% pages, run **OCR** branch (PaddleOCR) reusing Parser stack from product spec — **defer** unless blocked; record in README as Phase 2.

---

## Chunk 4: Skill candidates and CT alignment

### Task 6: Draft skill rows from segments

**Files:**
- Create: `master/skill_pipeline/draft_skills.py`
- Create: `data/knowledge_graph/draft/.gitkeep`

- [ ] **Step 1: For each `Segment` at lesson level (e.g. “Bài”), emit a **draft** row:**

```yaml
skill_id: null
grade: 10
domain: TBD
title_vi: "Bài 2: ..."
chapter_label: "Chương 1"
aliases: []
sgk_refs:
  - publisher: "KNTT"
    grade: 10
    path: "Phần Đại số > Chương 1 > Bài 2"
status: draft
provenance:
  source_pdf_sha256: "..."
  page_range: "12-18"
```

- [ ] **Step 2: CLI** `python -m master.skill_pipeline.cli draft --pdf path/to.pdf --publisher KNTT --grade 10 --out data/knowledge_graph/draft/kntt_g10_draft.yaml`

- [ ] **Step 3: Commit**

```bash
git add master/skill_pipeline/draft_skills.py master/skill_pipeline/cli.py data/knowledge_graph/draft/.gitkeep
git commit -m "feat(skill-pipeline): emit draft YAML per SGK lesson segment"
```

### Task 7: Alignment to CTGDPT (manual + assisted)

**Files:**
- Create: `data/knowledge_graph/math_ct_skills.yaml` (seed with **one** approved skill for CI)
- Create: `master/skill_pipeline/align_ct.py`

**Rule:** Không tự sinh `skill_id` bừa bãi. Pipeline chỉ:

1. Load existing `math_ct_skills.yaml` (authoritative CT list — initially curated by hand from official CT PDFs per [2026-04-14-sgk-math-knowledge-graph.md](docs/superpowers/plans/2026-04-14-sgk-math-knowledge-graph.md) Task 2).
2. For each draft row, compute **similarity** (embedding cosine or fuzzy string match on `title_vi` + `aliases`) to pick **best CT skill** if score > threshold; else flag `status: needs_review`.

```python
# master/skill_pipeline/align_ct.py (minimal stub)
from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher


@dataclass
class AlignmentResult:
    draft_title: str
    matched_skill_id: str | None
    score: float


def fuzzy_best_match(draft_title: str, canonical_titles: dict[str, str]) -> AlignmentResult:
    best_id, best_score = None, 0.0
    for skill_id, title in canonical_titles.items():
        s = SequenceMatcher(None, draft_title.lower(), title.lower()).ratio()
        if s > best_score:
            best_id, best_score = skill_id, s
    return AlignmentResult(draft_title=draft_title, matched_skill_id=best_id if best_score >= 0.82 else None, score=best_score)
```

- [ ] **Step 1: Test** `fuzzy_best_match` with known pairs.

- [ ] **Step 2: Optional LLM step** — only if fuzzy fails: call OpenAI-compatible JSON mode to suggest `skill_id` from a **fixed enum list** loaded from `math_ct_skills.yaml` (no free-form ids). Document env vars in README.

- [ ] **Step 3: Commit**

```bash
git add master/skill_pipeline/align_ct.py data/knowledge_graph/math_ct_skills.yaml tests/test_align_ct.py
git commit -m "feat(skill-pipeline): align draft segments to CT skill table"
```

---

## Chunk 5: Validation, edges, handoff to KG

### Task 8: Validate YAML against schema

**Files:**
- Create: `master/skill_pipeline/validate_skills.py`

- [ ] Use `jsonschema` or `pydantic` to validate each record. Add `jsonschema` to `requirements.txt` if not present.

```bash
pytest tests/test_validate_skills.py -v
git add master/skill_pipeline/validate_skills.py requirements.txt tests/test_validate_skills.py
git commit -m "feat(skill-pipeline): validate skill YAML against skill_record schema"
```

### Task 9: Prerequisite edges (semi-automatic)

**Files:**
- Append: `data/knowledge_graph/math_ct_edges.yaml`

- [ ] **Rule:** Within cùng chương, thứ tự **Bài** tăng dần → cạnh `PREREQUISITE` giữa skill liền kề **chỉ khi** CT implies sequence; otherwise chỉ gắn `SAME_TOPIC_FAMILY` hoặc bỏ qua. **Bắt buộc review người** trước khi merge.

- [ ] Script: `python -m master.skill_pipeline.cli propose-edges --skills data/knowledge_graph/draft/aligned.yaml --out data/knowledge_graph/draft/edges_proposed.yaml`

- [ ] **Commit** after human edits.

### Task 10: Handoff

- [ ] Import approved YAML into NetworkX or Neo4j per [2026-04-14-sgk-math-knowledge-graph.md](docs/superpowers/plans/2026-04-14-sgk-math-knowledge-graph.md) Task 5.
- [ ] Link `QuestionExam.skill_ids` tagging workflow (manual or crawler post-process).

---

## Plan review checklist (author)

- [ ] Every chunk maps to spec §4.4 (CT anchor, SGK as evidence).
- [ ] No placeholder steps without commands or code.
- [ ] Import paths adjusted to actual package layout (`master/skill_pipeline/` recommended).

---

## Execution handoff

Plan saved to `docs/superpowers/plans/2026-04-14-pdf-to-skill-set-pipeline.md`. Ready to execute?

If your harness supports subagents: use **superpowers:subagent-driven-development** — one task per chunk, review between chunks.

If not: use **superpowers:executing-plans** with checkpoints after Chunk 2 (text extraction works) and Chunk 4 (alignment produces reviewable YAML).
