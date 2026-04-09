# Module B: Grading Pipeline — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Parser Agent (image → structured exam JSON), Teacher Agent (grading + error analysis), Verifier Agent (independent verification + debate), and Grading Engine (SymPy math verification).

**Architecture:** A 4-stage pipeline: Parser extracts questions from images/PDFs using OpenCV + PaddleOCR, Teacher grades using LLM + exact match + SymPy, Verifier independently grades and debates disagreements with Teacher, Grading Engine provides sandboxed math verification.

**Tech Stack:** Python 3.11+, PaddleOCR, PaddlePaddle, OpenCV, NumPy, SymPy, FastAPI, httpx

**Owner:** Phúc (AI Core 2)

**Dependency:** Wait for Khang to complete `common/` (Day 2). Start `preprocessing.py` on Day 1 (no LLM needed).

---

## File Structure

```
master/agents/src/
├── parser/
│   ├── __init__.py
│   ├── preprocessing.py           ← OpenCV: gray, denoise, deskew
│   ├── ocr.py                     ← PaddleOCR wrapper
│   ├── extractor.py               ← Question extraction + structuring
│   └── agent.py                   ← ParserAgent class
├── teacher/
│   ├── __init__.py
│   ├── grading.py                 ← Per-type grading strategies
│   ├── error_analysis.py          ← Error taxonomy classification
│   └── agent.py                   ← TeacherAgent class
└── verifier/
    ├── __init__.py
    ├── discrepancy.py             ← Diff detection between evaluations
    ├── debate.py                  ← Multi-round debate protocol
    └── agent.py                   ← VerifierAgent class

master/apps/grading-engine/
├── main.py                        ← FastAPI at port 8001
├── sympy_grader.py                ← SymPy expression verification
├── requirements.txt
└── Dockerfile
```

---

## Chunk 1: Parser Agent

### Task 1: Install PaddleOCR Dependencies

**Files:**
- Modify: `master/agents/requirements.txt` (add OCR dependencies)

- [ ] **Step 1: Add Parser dependencies to requirements.txt**

Append these to `master/agents/requirements.txt`:

```txt
# Parser Agent dependencies
opencv-python-headless>=4.9.0
numpy>=1.26.0
paddlepaddle>=2.6.0
paddleocr>=2.9.0
Pillow>=10.0.0
```

- [ ] **Step 2: Install**

Run:
```bash
cd master/agents
source .venv/bin/activate
pip install -r requirements.txt
```

Expected: All packages install. PaddleOCR downloads on first use.

- [ ] **Step 3: Commit**

```bash
git add master/agents/requirements.txt
git commit -m "feat(parser): add PaddleOCR and OpenCV dependencies"
```

---

### Task 2: Image Preprocessing — `parser/preprocessing.py`

**Files:**
- Create: `master/agents/src/parser/__init__.py`
- Create: `master/agents/src/parser/preprocessing.py`
- Test: `master/agents/tests/test_parser.py`

> **No LLM dependency** — Phúc can start this on Day 1.

- [ ] **Step 1: Write the failing test**

```python
# master/agents/tests/test_parser.py
import numpy as np
import pytest
from src.parser.preprocessing import ImagePreprocessor


@pytest.fixture
def preprocessor():
    return ImagePreprocessor()


@pytest.fixture
def sample_image():
    """Create a simple test image: white background, some gray text-like regions."""
    img = np.ones((400, 300, 3), dtype=np.uint8) * 255
    img[50:70, 30:270] = 100  # simulate text line
    img[100:120, 30:270] = 100
    img[150:170, 30:270] = 80
    return img


def test_to_grayscale(preprocessor, sample_image):
    gray = preprocessor.to_grayscale(sample_image)
    assert len(gray.shape) == 2, "Should be 2D (grayscale)"
    assert gray.shape == (400, 300)


def test_denoise(preprocessor, sample_image):
    gray = preprocessor.to_grayscale(sample_image)
    denoised = preprocessor.denoise(gray)
    assert denoised.shape == gray.shape
    assert denoised.dtype == np.uint8


def test_binarize(preprocessor, sample_image):
    gray = preprocessor.to_grayscale(sample_image)
    binary = preprocessor.binarize(gray)
    unique_vals = np.unique(binary)
    assert all(v in [0, 255] for v in unique_vals), "Binary image should only have 0 and 255"


def test_enhance_contrast(preprocessor, sample_image):
    gray = preprocessor.to_grayscale(sample_image)
    enhanced = preprocessor.enhance_contrast(gray)
    assert enhanced.shape == gray.shape


def test_full_pipeline(preprocessor, sample_image):
    result = preprocessor.process(sample_image)
    assert len(result.shape) == 2
    assert result.dtype == np.uint8
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd master/agents && python -m pytest tests/test_parser.py -v`
Expected: FAIL — ImportError

- [ ] **Step 3: Write implementation**

```python
# master/agents/src/parser/__init__.py
# (empty)
```

```python
# master/agents/src/parser/preprocessing.py
from __future__ import annotations

import cv2
import numpy as np


class ImagePreprocessor:
    """OpenCV-based image preprocessing for OCR optimization."""

    def to_grayscale(self, image: np.ndarray) -> np.ndarray:
        if len(image.shape) == 3:
            return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return image

    def denoise(self, gray: np.ndarray) -> np.ndarray:
        return cv2.fastNlMeansDenoising(gray, h=10, templateWindowSize=7, searchWindowSize=21)

    def binarize(self, gray: np.ndarray) -> np.ndarray:
        return cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )

    def enhance_contrast(self, gray: np.ndarray) -> np.ndarray:
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        return clahe.apply(gray)

    def deskew(self, gray: np.ndarray) -> np.ndarray:
        """Correct slight rotation in scanned images."""
        coords = np.column_stack(np.where(gray < 128))
        if len(coords) < 100:
            return gray
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
        if abs(angle) < 0.5:
            return gray
        h, w = gray.shape
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        return cv2.warpAffine(gray, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

    def process(self, image: np.ndarray) -> np.ndarray:
        """Full preprocessing pipeline: grayscale → denoise → enhance → binarize."""
        gray = self.to_grayscale(image)
        denoised = self.denoise(gray)
        enhanced = self.enhance_contrast(denoised)
        binary = self.binarize(enhanced)
        return binary
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd master/agents && python -m pytest tests/test_parser.py -v`
Expected: 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add master/agents/src/parser/ master/agents/tests/test_parser.py
git commit -m "feat(parser): add ImagePreprocessor with grayscale, denoise, binarize, deskew"
```

---

### Task 3: PaddleOCR Wrapper — `parser/ocr.py`

**Files:**
- Create: `master/agents/src/parser/ocr.py`

- [ ] **Step 1: Write implementation**

```python
# master/agents/src/parser/ocr.py
from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class TextBlock:
    """A detected text region from OCR."""
    text: str
    bbox: list[list[float]]   # [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
    confidence: float
    line_index: int = 0       # reading order

    @property
    def top_y(self) -> float:
        return min(p[1] for p in self.bbox)

    @property
    def left_x(self) -> float:
        return min(p[0] for p in self.bbox)


class OCREngine:
    """PaddleOCR wrapper for Vietnamese text recognition."""

    def __init__(self, lang: str = "vi", use_gpu: bool = False):
        self._lang = lang
        self._use_gpu = use_gpu
        self._ocr = None  # lazy init (PaddleOCR is heavy)

    def _ensure_loaded(self):
        if self._ocr is None:
            from paddleocr import PaddleOCR
            self._ocr = PaddleOCR(
                lang=self._lang,
                use_angle_cls=True,
                use_gpu=self._use_gpu,
                show_log=False,
            )
            logger.info("PaddleOCR initialized (lang=%s, gpu=%s)", self._lang, self._use_gpu)

    def extract(self, image: np.ndarray) -> list[TextBlock]:
        """Run OCR on an image and return sorted text blocks."""
        self._ensure_loaded()
        results = self._ocr.ocr(image, cls=True)

        blocks: list[TextBlock] = []
        if not results or not results[0]:
            return blocks

        for line in results[0]:
            bbox = line[0]
            text = line[1][0]
            confidence = line[1][1]
            blocks.append(TextBlock(text=text, bbox=bbox, confidence=confidence))

        # Sort by reading order: top-to-bottom, left-to-right
        blocks.sort(key=lambda b: (b.top_y, b.left_x))
        for i, block in enumerate(blocks):
            block.line_index = i

        return blocks

    def extract_text(self, image: np.ndarray) -> str:
        """Extract plain text from image, lines joined by newlines."""
        blocks = self.extract(image)
        return "\n".join(b.text for b in blocks)
```

- [ ] **Step 2: Commit**

```bash
git add master/agents/src/parser/ocr.py
git commit -m "feat(parser): add PaddleOCR wrapper with TextBlock extraction"
```

---

### Task 4: Question Extractor — `parser/extractor.py`

**Files:**
- Create: `master/agents/src/parser/extractor.py`

- [ ] **Step 1: Write implementation**

```python
# master/agents/src/parser/extractor.py
from __future__ import annotations

import re
import uuid
import logging
from typing import Any

from ..common.llm_client import LLMClient
from ..common.message import ExamQuestion, ExamSection, ExamData

logger = logging.getLogger(__name__)

MC_PATTERN = re.compile(
    r"(?:Câu|câu|Question|Q)\s*(\d+)[.:]?\s*(.*?)(?=(?:Câu|câu|Question|Q)\s*\d+[.:]|\Z)",
    re.DOTALL | re.IGNORECASE,
)

OPTION_PATTERN = re.compile(
    r"([A-D])[.)]\s*(.*?)(?=(?:[A-D][.)]|\Z))",
    re.DOTALL,
)


def extract_questions_by_regex(raw_text: str) -> list[dict[str, Any]]:
    """Rule-based question extraction from OCR text.

    Works well for standard Vietnamese exam formats with
    "Câu N:" prefix and A/B/C/D options.
    """
    questions: list[dict] = []
    matches = MC_PATTERN.findall(raw_text)

    for idx_str, body in matches:
        q_index = int(idx_str)
        body = body.strip()

        options_matches = OPTION_PATTERN.findall(body)
        if options_matches:
            content = body[:body.find(options_matches[0][0] + ".")].strip()
            if not content:
                content = body[:body.find(options_matches[0][0] + ")")].strip()
            options = [f"{letter}. {text.strip()}" for letter, text in options_matches]
            q_type = "multiple_choice"
        else:
            content = body
            options = None
            q_type = "essay"

        questions.append({
            "id": f"q{q_index}",
            "question_index": q_index,
            "type": q_type,
            "content": content,
            "options": options,
            "topic_tags": [],
            "max_score": 0.2 if q_type == "multiple_choice" else 1.0,
        })

    return questions


async def extract_questions_with_llm(
    raw_text: str, llm: LLMClient, subject: str = "math"
) -> list[dict[str, Any]]:
    """LLM-assisted question extraction for complex or unusual formats."""
    prompt = f"""You are an exam question extractor. Given the following OCR text from a Vietnamese {subject} exam, extract all questions into structured JSON.

OCR Text:
---
{raw_text[:4000]}
---

Return a JSON array where each element has:
- "id": "q1", "q2", etc.
- "question_index": integer
- "type": "multiple_choice" or "essay"
- "content": the question text
- "options": ["A. ...", "B. ...", "C. ...", "D. ..."] for MC, null for essay
- "topic_tags": [] (leave empty)
- "max_score": 0.2 for MC, 1.0 for essay

Return ONLY valid JSON array."""

    result = await llm.chat_json([{"role": "user", "content": prompt}])
    if isinstance(result, list):
        return result
    return result.get("questions", [])


def build_exam_data(
    questions: list[dict],
    subject: str = "math",
    exam_type: str = "THPTQG",
    source: str = "image",
) -> ExamData:
    """Assemble extracted questions into the canonical ExamData schema."""
    mc_questions = []
    essay_questions = []

    for q in questions:
        eq = ExamQuestion(
            id=q.get("id", f"q{q.get('question_index', 0)}"),
            question_index=q.get("question_index", 0),
            type=q.get("type", "multiple_choice"),
            content=q.get("content", ""),
            content_latex=q.get("content_latex"),
            options=q.get("options"),
            correct_answer=q.get("correct_answer"),
            has_image=q.get("has_image", False),
            topic_tags=q.get("topic_tags", []),
            max_score=q.get("max_score", 0.2),
        )
        if eq.type == "multiple_choice":
            mc_questions.append(eq)
        else:
            essay_questions.append(eq)

    sections = []
    if mc_questions:
        sections.append(ExamSection(type="multiple_choice", questions=mc_questions))
    if essay_questions:
        sections.append(ExamSection(type="essay", questions=essay_questions))

    return ExamData(
        exam_id=str(uuid.uuid4()),
        source=source,
        subject=subject,
        exam_type=exam_type,
        total_questions=len(questions),
        sections=sections,
    )
```

- [ ] **Step 2: Commit**

```bash
git add master/agents/src/parser/extractor.py
git commit -m "feat(parser): add question extractor with regex + LLM fallback"
```

---

### Task 5: Parser Agent — `parser/agent.py`

**Files:**
- Create: `master/agents/src/parser/agent.py`

- [ ] **Step 1: Write implementation**

```python
# master/agents/src/parser/agent.py
from __future__ import annotations

import logging
from typing import Any
from pathlib import Path

import cv2
import numpy as np

from ..base_agent import BaseAgent
from ..common.llm_client import LLMClient
from .preprocessing import ImagePreprocessor
from .ocr import OCREngine
from .extractor import extract_questions_by_regex, extract_questions_with_llm, build_exam_data

logger = logging.getLogger(__name__)


class ParserAgent(BaseAgent):
    """Processes exam images/PDFs into structured ExamData JSON."""

    def __init__(self, llm_client: LLMClient, use_gpu_ocr: bool = False):
        super().__init__(name="parser", llm_client=llm_client)
        self.preprocessor = ImagePreprocessor()
        self.ocr = OCREngine(lang="vi", use_gpu=use_gpu_ocr)

    @property
    def system_prompt(self) -> str:
        return (
            "You are the Parser Agent. Your job is to extract questions from "
            "exam images. You use OCR to read text, then structure it into "
            "the canonical ExamData JSON format."
        )

    @property
    def description(self) -> str:
        return "Extracts structured exam data from images using OCR + NLP."

    async def handle(self, payload: dict[str, Any]) -> dict[str, Any]:
        action = payload.get("action", "parse_image")
        request = payload.get("request", {})
        metadata = request.get("metadata", {})
        file_urls = request.get("file_urls", [])

        if not file_urls:
            return {"error": "No file_urls provided for parsing"}

        all_text_parts: list[str] = []
        for file_url in file_urls:
            text = self._process_single_image(file_url)
            all_text_parts.append(text)

        raw_text = "\n".join(all_text_parts)
        logger.info("[parser] OCR extracted %d characters", len(raw_text))

        questions = extract_questions_by_regex(raw_text)

        if not questions:
            logger.info("[parser] Regex extraction found 0 questions, trying LLM")
            questions = await extract_questions_with_llm(
                raw_text, self._llm,
                subject=metadata.get("subject", "math"),
            )

        exam_data = build_exam_data(
            questions=questions,
            subject=metadata.get("subject", "math"),
            exam_type=metadata.get("exam_type", "THPTQG"),
            source="image",
        )

        logger.info("[parser] Extracted %d questions", exam_data.total_questions)
        return {"exam_data": exam_data.model_dump(), "raw_text": raw_text}

    def _process_single_image(self, file_path: str) -> str:
        """Load, preprocess, and OCR a single image file."""
        img = cv2.imread(file_path)
        if img is None:
            logger.error("Failed to load image: %s", file_path)
            return ""

        processed = self.preprocessor.process(img)
        return self.ocr.extract_text(processed)
```

- [ ] **Step 2: Commit**

```bash
git add master/agents/src/parser/agent.py
git commit -m "feat(parser): add ParserAgent — image preprocessing → OCR → question extraction"
```

---

## Chunk 2: Teacher Agent

### Task 6: Grading Logic — `teacher/grading.py`

**Files:**
- Create: `master/agents/src/teacher/__init__.py`
- Create: `master/agents/src/teacher/grading.py`
- Test: `master/agents/tests/test_teacher.py`

- [ ] **Step 1: Write the failing test**

```python
# master/agents/tests/test_teacher.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.teacher.grading import (
    grade_multiple_choice,
    GradingResult,
)


def test_grade_mc_correct():
    result = grade_multiple_choice(
        student_answer="A",
        correct_answer="A",
        max_score=0.2,
    )
    assert result.is_correct is True
    assert result.score == 0.2
    assert "đúng" in result.reasoning.lower() or "correct" in result.reasoning.lower()


def test_grade_mc_wrong():
    result = grade_multiple_choice(
        student_answer="B",
        correct_answer="A",
        max_score=0.2,
    )
    assert result.is_correct is False
    assert result.score == 0.0


def test_grade_mc_none_answer():
    result = grade_multiple_choice(
        student_answer=None,
        correct_answer="A",
        max_score=0.2,
    )
    assert result.is_correct is False
    assert result.score == 0.0
    assert "không trả lời" in result.reasoning.lower() or "no answer" in result.reasoning.lower()


def test_grade_mc_case_insensitive():
    result = grade_multiple_choice(
        student_answer="a",
        correct_answer="A",
        max_score=0.2,
    )
    assert result.is_correct is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd master/agents && python -m pytest tests/test_teacher.py -v`
Expected: FAIL

- [ ] **Step 3: Write implementation**

```python
# master/agents/src/teacher/__init__.py
# (empty)
```

```python
# master/agents/src/teacher/grading.py
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

from ..common.llm_client import LLMClient
from ..common.message import ErrorType

logger = logging.getLogger(__name__)


@dataclass
class GradingResult:
    question_id: str = ""
    student_answer: Optional[str] = None
    correct_answer: Optional[str] = None
    is_correct: bool = False
    score: float = 0.0
    max_score: float = 0.2
    reasoning: str = ""
    error_type: Optional[ErrorType] = None
    root_cause: Optional[str] = None
    knowledge_component: Optional[str] = None
    remedial: Optional[str] = None


def grade_multiple_choice(
    student_answer: Optional[str],
    correct_answer: str,
    max_score: float = 0.2,
) -> GradingResult:
    """Exact match grading for multiple choice questions."""
    if student_answer is None or student_answer.strip() == "":
        return GradingResult(
            student_answer=student_answer,
            correct_answer=correct_answer,
            is_correct=False,
            score=0.0,
            max_score=max_score,
            reasoning="Không trả lời (no answer provided).",
        )

    is_correct = student_answer.strip().upper() == correct_answer.strip().upper()
    score = max_score if is_correct else 0.0
    reasoning = (
        f"Đáp án đúng: {correct_answer}."
        if is_correct
        else f"Đáp án sai. Học sinh chọn {student_answer}, đáp án đúng là {correct_answer}."
    )

    return GradingResult(
        student_answer=student_answer,
        correct_answer=correct_answer,
        is_correct=is_correct,
        score=score,
        max_score=max_score,
        reasoning=reasoning,
    )


async def grade_essay_with_llm(
    question_content: str,
    student_answer: str,
    correct_answer: Optional[str],
    rubric: Optional[str],
    max_score: float,
    llm: LLMClient,
    topic_tags: list[str] | None = None,
) -> GradingResult:
    """LLM-as-a-judge grading for essay/free-response questions."""
    rubric_section = f"\nRubric:\n{rubric}" if rubric else ""
    answer_key = f"\nĐáp án tham khảo:\n{correct_answer}" if correct_answer else ""

    prompt = f"""Bạn là giáo viên chấm bài thi THPT. Hãy chấm bài làm sau đây.

**Câu hỏi:**
{question_content}
{answer_key}
{rubric_section}

**Bài làm của học sinh:**
{student_answer}

**Điểm tối đa:** {max_score}

Trả lời bằng JSON với format:
{{
  "score": <float>,
  "is_correct": <bool>,
  "reasoning": "<giải thích chi tiết việc chấm điểm>",
  "error_type": "<CONCEPT_GAP|CALCULATION_ERROR|INCOMPLETE_REASONING|MISINTERPRETATION|PRESENTATION_FLAW|null>",
  "root_cause": "<nguyên nhân lỗi hoặc null>",
  "remedial": "<gợi ý ôn tập hoặc null>"
}}"""

    result = await llm.chat_json([{"role": "user", "content": prompt}])

    error_type = None
    if result.get("error_type") and result["error_type"] != "null":
        try:
            error_type = ErrorType(result["error_type"])
        except ValueError:
            pass

    return GradingResult(
        student_answer=student_answer,
        correct_answer=correct_answer,
        is_correct=result.get("is_correct", False),
        score=min(float(result.get("score", 0)), max_score),
        max_score=max_score,
        reasoning=result.get("reasoning", ""),
        error_type=error_type,
        root_cause=result.get("root_cause"),
        knowledge_component=topic_tags[0] if topic_tags else None,
        remedial=result.get("remedial"),
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd master/agents && python -m pytest tests/test_teacher.py -v`
Expected: 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add master/agents/src/teacher/ master/agents/tests/test_teacher.py
git commit -m "feat(teacher): add MC exact-match grading and LLM essay grading"
```

---

### Task 7: Error Analysis — `teacher/error_analysis.py`

**Files:**
- Create: `master/agents/src/teacher/error_analysis.py`

- [ ] **Step 1: Write implementation**

```python
# master/agents/src/teacher/error_analysis.py
from __future__ import annotations

from ..common.message import ErrorType, ErrorAnalysis
from ..common.llm_client import LLMClient


ERROR_DESCRIPTIONS = {
    ErrorType.CONCEPT_GAP: "Hổng kiến thức nền tảng",
    ErrorType.CALCULATION_ERROR: "Sai số tính toán",
    ErrorType.INCOMPLETE_REASONING: "Thiếu bước trung gian trong lời giải",
    ErrorType.MISINTERPRETATION: "Hiểu sai đề bài",
    ErrorType.PRESENTATION_FLAW: "Trình bày không rõ ràng, thiếu ký hiệu",
}


def build_error_analysis(
    error_type: ErrorType | None,
    root_cause: str | None,
    knowledge_component: str | None,
    remedial: str | None,
) -> ErrorAnalysis | None:
    """Build an ErrorAnalysis object from grading result fields."""
    if error_type is None:
        return None
    return ErrorAnalysis(
        error_type=error_type,
        root_cause=root_cause or ERROR_DESCRIPTIONS.get(error_type, "Unknown"),
        knowledge_component=knowledge_component or "unknown",
        remedial=remedial or f"Ôn lại phần: {ERROR_DESCRIPTIONS.get(error_type, '')}",
    )


async def classify_error_with_llm(
    question: str,
    student_answer: str,
    correct_answer: str,
    llm: LLMClient,
) -> ErrorAnalysis | None:
    """Use LLM to classify the error type for a wrong answer."""
    prompt = f"""Phân tích lỗi sai của học sinh.

Câu hỏi: {question}
Đáp án đúng: {correct_answer}
Bài làm: {student_answer}

Phân loại lỗi vào MỘT trong 5 loại:
- CONCEPT_GAP: Hổng kiến thức nền tảng
- CALCULATION_ERROR: Sai số tính toán
- INCOMPLETE_REASONING: Thiếu bước trung gian
- MISINTERPRETATION: Hiểu sai đề bài
- PRESENTATION_FLAW: Trình bày không rõ ràng

Trả lời JSON:
{{"error_type": "...", "root_cause": "...", "knowledge_component": "...", "remedial": "..."}}"""

    result = await llm.chat_json([{"role": "user", "content": prompt}])

    try:
        error_type = ErrorType(result.get("error_type", "CONCEPT_GAP"))
    except ValueError:
        error_type = ErrorType.CONCEPT_GAP

    return ErrorAnalysis(
        error_type=error_type,
        root_cause=result.get("root_cause", ""),
        knowledge_component=result.get("knowledge_component", "unknown"),
        remedial=result.get("remedial", ""),
    )
```

- [ ] **Step 2: Commit**

```bash
git add master/agents/src/teacher/error_analysis.py
git commit -m "feat(teacher): add error analysis with 5-type taxonomy"
```

---

### Task 8: Teacher Agent — `teacher/agent.py`

**Files:**
- Create: `master/agents/src/teacher/agent.py`

- [ ] **Step 1: Write implementation**

```python
# master/agents/src/teacher/agent.py
from __future__ import annotations

import logging
import uuid
from typing import Any, Optional

from ..base_agent import BaseAgent
from ..common.llm_client import LLMClient
from ..common.message import (
    QuestionEvaluation, EvaluationResult, OverallAnalysis,
    ErrorAnalysis, ExamData, ExamQuestion,
)
from .grading import grade_multiple_choice, grade_essay_with_llm
from .error_analysis import build_error_analysis, classify_error_with_llm

logger = logging.getLogger(__name__)


class TeacherAgent(BaseAgent):
    """Grades student submissions and produces detailed evaluation."""

    def __init__(self, llm_client: LLMClient, grading_engine_url: str = "http://localhost:8001"):
        super().__init__(name="teacher", llm_client=llm_client)
        self._grading_engine_url = grading_engine_url

    @property
    def system_prompt(self) -> str:
        return (
            "You are the Teacher Agent of MASTER. You grade student exam submissions "
            "using rubrics, provide detailed feedback, and classify errors into the "
            "5-type error taxonomy. Be fair, precise, and educational."
        )

    @property
    def description(self) -> str:
        return "Grades exams with exact match + LLM + SymPy, and produces error analysis."

    async def handle(self, payload: dict[str, Any]) -> dict[str, Any]:
        action = payload.get("action", "grade")
        if action == "grade":
            return await self._grade(payload)
        elif action == "generate_hint":
            return await self._generate_hint(payload)
        return {"error": f"Unknown action: {action}"}

    async def _grade(self, payload: dict[str, Any]) -> dict[str, Any]:
        context = payload.get("context", {})
        request = payload.get("request", {})

        parser_result = context.get("parser", {})
        exam_data_raw = parser_result.get("exam_data", {})
        student_answers: dict[str, str] = request.get("metadata", {}).get("student_answers", {})

        questions = self._flatten_questions(exam_data_raw)
        per_question: list[dict] = []
        total_score = 0.0
        max_score_total = 0.0
        topic_results: dict[str, list[bool]] = {}

        for q in questions:
            q_id = q.get("id", "")
            q_type = q.get("type", "multiple_choice")
            student_ans = student_answers.get(q_id)
            correct_ans = q.get("correct_answer")
            q_max = q.get("max_score", 0.2)
            topic_tags = q.get("topic_tags", [])

            if q_type == "multiple_choice":
                result = grade_multiple_choice(student_ans, correct_ans or "", q_max)
            else:
                result = await grade_essay_with_llm(
                    question_content=q.get("content", ""),
                    student_answer=student_ans or "",
                    correct_answer=correct_ans,
                    rubric=None,
                    max_score=q_max,
                    llm=self._llm,
                    topic_tags=topic_tags,
                )

            error_analysis = None
            if not result.is_correct and result.error_type:
                error_analysis = build_error_analysis(
                    result.error_type, result.root_cause,
                    result.knowledge_component, result.remedial,
                )
            elif not result.is_correct and q_type == "multiple_choice":
                error_analysis_obj = await classify_error_with_llm(
                    q.get("content", ""), student_ans or "", correct_ans or "", self._llm
                )
                error_analysis = error_analysis_obj

            q_eval = QuestionEvaluation(
                question_id=q_id,
                student_answer=student_ans,
                correct_answer=correct_ans,
                is_correct=result.is_correct,
                score=result.score,
                max_score=q_max,
                reasoning=result.reasoning,
                error_analysis=error_analysis,
            )
            per_question.append(q_eval.model_dump())
            total_score += result.score
            max_score_total += q_max

            for tag in topic_tags:
                topic_results.setdefault(tag, []).append(result.is_correct)

        strengths = [t for t, results in topic_results.items() if sum(results) / len(results) >= 0.7]
        weaknesses = [t for t, results in topic_results.items() if sum(results) / len(results) < 0.5]

        evaluation = EvaluationResult(
            evaluation_id=str(uuid.uuid4()),
            exam_id=exam_data_raw.get("exam_id", ""),
            student_id=request.get("student_id", ""),
            total_score=round(total_score, 2),
            max_score=round(max_score_total, 2),
            confidence=0.85,
            per_question=per_question,
            overall_analysis=OverallAnalysis(
                strengths=strengths,
                weaknesses=weaknesses,
                recommended_topics=weaknesses[:5],
            ),
        )

        return {"evaluation": evaluation.model_dump()}

    async def _generate_hint(self, payload: dict[str, Any]) -> dict[str, Any]:
        request = payload.get("request", {})
        metadata = request.get("metadata", {})
        question_content = metadata.get("question_content", "")

        if not question_content:
            return {"hint": "Vui lòng cung cấp nội dung câu hỏi."}

        hint = await self.think(
            f"Hãy đưa ra gợi ý (hint) cho học sinh về câu hỏi sau, "
            f"KHÔNG cho đáp án trực tiếp, chỉ hướng dẫn cách tiếp cận:\n\n{question_content}"
        )
        return {"hint": hint}

    @staticmethod
    def _flatten_questions(exam_data: dict) -> list[dict]:
        questions = []
        for section in exam_data.get("sections", []):
            questions.extend(section.get("questions", []))
        return questions
```

- [ ] **Step 2: Commit**

```bash
git add master/agents/src/teacher/agent.py
git commit -m "feat(teacher): add TeacherAgent with MC + essay grading and error analysis"
```

---

## Chunk 3: Verifier Agent

### Task 9: Discrepancy Detection — `verifier/discrepancy.py`

**Files:**
- Create: `master/agents/src/verifier/__init__.py`
- Create: `master/agents/src/verifier/discrepancy.py`
- Test: `master/agents/tests/test_verifier.py`

- [ ] **Step 1: Write the failing test**

```python
# master/agents/tests/test_verifier.py
import pytest
from src.verifier.discrepancy import find_discrepancies, DiscrepancyType


def test_find_score_mismatch():
    teacher_eval = [
        {"question_id": "q1", "score": 0.2, "is_correct": True, "error_analysis": None},
    ]
    verifier_eval = [
        {"question_id": "q1", "score": 0.0, "is_correct": False, "error_analysis": None},
    ]
    discs = find_discrepancies(teacher_eval, verifier_eval)
    assert len(discs) == 1
    assert discs[0].type == DiscrepancyType.SCORE_MISMATCH


def test_no_discrepancy_when_agree():
    teacher_eval = [
        {"question_id": "q1", "score": 0.2, "is_correct": True, "error_analysis": None},
    ]
    verifier_eval = [
        {"question_id": "q1", "score": 0.2, "is_correct": True, "error_analysis": None},
    ]
    discs = find_discrepancies(teacher_eval, verifier_eval)
    assert len(discs) == 0


def test_find_error_type_conflict():
    teacher_eval = [
        {
            "question_id": "q1", "score": 0.0, "is_correct": False,
            "error_analysis": {"error_type": "CONCEPT_GAP"},
        },
    ]
    verifier_eval = [
        {
            "question_id": "q1", "score": 0.0, "is_correct": False,
            "error_analysis": {"error_type": "CALCULATION_ERROR"},
        },
    ]
    discs = find_discrepancies(teacher_eval, verifier_eval)
    assert any(d.type == DiscrepancyType.ERROR_TYPE_CONFLICT for d in discs)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd master/agents && python -m pytest tests/test_verifier.py -v`
Expected: FAIL

- [ ] **Step 3: Write implementation**

```python
# master/agents/src/verifier/__init__.py
# (empty)
```

```python
# master/agents/src/verifier/discrepancy.py
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class DiscrepancyType(str, Enum):
    SCORE_MISMATCH = "SCORE_MISMATCH"
    ERROR_TYPE_CONFLICT = "ERROR_TYPE_CONFLICT"
    REASONING_FLAW = "REASONING_FLAW"
    MISSED_PARTIAL_CREDIT = "MISSED_PARTIAL_CREDIT"


@dataclass
class Discrepancy:
    question_id: str
    type: DiscrepancyType
    teacher_value: Any
    verifier_value: Any
    description: str


def find_discrepancies(
    teacher_eval: list[dict],
    verifier_eval: list[dict],
    score_tolerance: float = 0.05,
) -> list[Discrepancy]:
    """Compare Teacher and Verifier evaluations, return list of disagreements."""
    teacher_map = {q["question_id"]: q for q in teacher_eval}
    verifier_map = {q["question_id"]: q for q in verifier_eval}

    discrepancies: list[Discrepancy] = []

    for q_id, t_eval in teacher_map.items():
        v_eval = verifier_map.get(q_id)
        if v_eval is None:
            continue

        # Score mismatch
        t_score = t_eval.get("score", 0)
        v_score = v_eval.get("score", 0)
        if abs(t_score - v_score) > score_tolerance:
            discrepancies.append(Discrepancy(
                question_id=q_id,
                type=DiscrepancyType.SCORE_MISMATCH,
                teacher_value=t_score,
                verifier_value=v_score,
                description=f"Score diff: Teacher={t_score}, Verifier={v_score}",
            ))

        # Correctness disagreement (subsume into SCORE_MISMATCH)
        t_correct = t_eval.get("is_correct")
        v_correct = v_eval.get("is_correct")
        if t_correct != v_correct and abs(t_score - v_score) <= score_tolerance:
            discrepancies.append(Discrepancy(
                question_id=q_id,
                type=DiscrepancyType.SCORE_MISMATCH,
                teacher_value=t_correct,
                verifier_value=v_correct,
                description=f"Correctness disagree: Teacher={t_correct}, Verifier={v_correct}",
            ))

        # Error type conflict
        t_err = (t_eval.get("error_analysis") or {}).get("error_type")
        v_err = (v_eval.get("error_analysis") or {}).get("error_type")
        if t_err and v_err and t_err != v_err:
            discrepancies.append(Discrepancy(
                question_id=q_id,
                type=DiscrepancyType.ERROR_TYPE_CONFLICT,
                teacher_value=t_err,
                verifier_value=v_err,
                description=f"Error type: Teacher={t_err}, Verifier={v_err}",
            ))

    return discrepancies
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd master/agents && python -m pytest tests/test_verifier.py -v`
Expected: 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add master/agents/src/verifier/ master/agents/tests/test_verifier.py
git commit -m "feat(verifier): add discrepancy detection — score mismatch + error type conflict"
```

---

### Task 10: Debate Protocol — `verifier/debate.py`

**Files:**
- Create: `master/agents/src/verifier/debate.py`

- [ ] **Step 1: Write implementation**

```python
# master/agents/src/verifier/debate.py
from __future__ import annotations

import logging
from typing import Any

from ..common.llm_client import LLMClient
from .discrepancy import Discrepancy, DiscrepancyType

logger = logging.getLogger(__name__)

MAX_DEBATE_ROUNDS = 3
CONFIDENCE_THRESHOLD = 0.7


async def resolve_discrepancy(
    disc: Discrepancy,
    question: dict,
    teacher_reasoning: str,
    verifier_reasoning: str,
    llm: LLMClient,
) -> dict[str, Any]:
    """Attempt to resolve a single discrepancy via evidence-grounded debate.

    Returns a resolution dict with the final score/error_type/reasoning.
    """
    prompt = f"""You are a senior math examiner resolving a grading disagreement.

**Question:** {question.get('content', '')}
**Correct Answer:** {question.get('correct_answer', 'N/A')}

**Teacher's grading:** Score={disc.teacher_value}, Reasoning: {teacher_reasoning}
**Verifier's grading:** Score={disc.verifier_value}, Reasoning: {verifier_reasoning}

**Discrepancy type:** {disc.type.value}

Decide which grading is more accurate. If neither is clearly correct, average the scores.

Respond with JSON:
{{
  "resolution": "ACCEPT_TEACHER" | "ACCEPT_VERIFIER" | "AVERAGE",
  "final_score": <float>,
  "reasoning": "<explain your decision>",
  "confidence": <float between 0 and 1>
}}"""

    result = await llm.chat_json([{"role": "user", "content": prompt}])
    return {
        "question_id": disc.question_id,
        "resolution": result.get("resolution", "AVERAGE"),
        "final_score": result.get("final_score", (disc.teacher_value + disc.verifier_value) / 2),
        "reasoning": result.get("reasoning", ""),
        "confidence": result.get("confidence", 0.5),
    }


async def run_debate(
    discrepancies: list[Discrepancy],
    questions_map: dict[str, dict],
    teacher_eval_map: dict[str, dict],
    verifier_eval_map: dict[str, dict],
    llm: LLMClient,
) -> list[dict[str, Any]]:
    """Run the full debate protocol for all discrepancies."""
    resolutions = []
    for disc in discrepancies:
        q = questions_map.get(disc.question_id, {})
        t_eval = teacher_eval_map.get(disc.question_id, {})
        v_eval = verifier_eval_map.get(disc.question_id, {})

        resolution = await resolve_discrepancy(
            disc=disc,
            question=q,
            teacher_reasoning=t_eval.get("reasoning", ""),
            verifier_reasoning=v_eval.get("reasoning", ""),
            llm=llm,
        )
        resolutions.append(resolution)

    return resolutions
```

- [ ] **Step 2: Commit**

```bash
git add master/agents/src/verifier/debate.py
git commit -m "feat(verifier): add evidence-grounded debate protocol for resolving disagreements"
```

---

### Task 11: Verifier Agent — `verifier/agent.py`

**Files:**
- Create: `master/agents/src/verifier/agent.py`

- [ ] **Step 1: Write implementation**

```python
# master/agents/src/verifier/agent.py
from __future__ import annotations

import logging
import uuid
from typing import Any

from ..base_agent import BaseAgent
from ..common.llm_client import LLMClient
from ..common.message import (
    QuestionEvaluation, EvaluationResult, OverallAnalysis,
)
from ..teacher.grading import grade_multiple_choice, grade_essay_with_llm
from .discrepancy import find_discrepancies
from .debate import run_debate

logger = logging.getLogger(__name__)


class VerifierAgent(BaseAgent):
    """Independent grading + debate protocol to ensure evaluation quality."""

    def __init__(self, llm_client: LLMClient):
        super().__init__(name="verifier", llm_client=llm_client)

    @property
    def system_prompt(self) -> str:
        return (
            "You are the Verifier Agent. You independently grade student work "
            "and compare with the Teacher's evaluation. When disagreements arise, "
            "you engage in evidence-grounded debate. Only claims backed by evidence "
            "(rubric citations, mathematical proofs) are valid."
        )

    @property
    def description(self) -> str:
        return "Cross-checks Teacher grading via independent evaluation and debate."

    async def handle(self, payload: dict[str, Any]) -> dict[str, Any]:
        context = payload.get("context", {})
        request = payload.get("request", {})

        teacher_result = context.get("teacher", {})
        teacher_evaluation = teacher_result.get("evaluation", {})
        teacher_per_q = teacher_evaluation.get("per_question", [])

        parser_result = context.get("parser", {})
        exam_data = parser_result.get("exam_data", {})
        student_answers = request.get("metadata", {}).get("student_answers", {})

        # Phase 1: Independent grading (only for MC in MVP to save time)
        questions = self._flatten_questions(exam_data)
        verifier_per_q = []

        for q in questions:
            q_id = q.get("id", "")
            if q.get("type") == "multiple_choice":
                result = grade_multiple_choice(
                    student_answers.get(q_id),
                    q.get("correct_answer", ""),
                    q.get("max_score", 0.2),
                )
                verifier_per_q.append({
                    "question_id": q_id,
                    "score": result.score,
                    "is_correct": result.is_correct,
                    "reasoning": result.reasoning,
                    "error_analysis": None,
                })
            else:
                # For essay: trust Teacher in MVP, skip independent re-grading
                teacher_q = next((tq for tq in teacher_per_q if tq.get("question_id") == q_id), None)
                if teacher_q:
                    verifier_per_q.append(teacher_q)

        # Phase 2: Discrepancy detection
        discrepancies = find_discrepancies(teacher_per_q, verifier_per_q)
        logger.info("[verifier] Found %d discrepancies", len(discrepancies))

        # Phase 3: Debate (if any disagreements)
        resolutions = []
        if discrepancies:
            questions_map = {q.get("id"): q for q in questions}
            teacher_map = {q["question_id"]: q for q in teacher_per_q}
            verifier_map = {q["question_id"]: q for q in verifier_per_q}

            resolutions = await run_debate(
                discrepancies, questions_map, teacher_map, verifier_map, self._llm,
            )

        # Phase 4: Merge into final evaluation
        final_per_q = self._merge_evaluations(teacher_per_q, resolutions)
        total_score = sum(q.get("score", 0) for q in final_per_q)
        max_score = sum(q.get("max_score", 0) for q in final_per_q)

        return {
            "evaluation": {
                **teacher_evaluation,
                "per_question": final_per_q,
                "total_score": round(total_score, 2),
                "max_score": round(max_score, 2),
                "verification": {
                    "discrepancies_found": len(discrepancies),
                    "resolutions": resolutions,
                },
            },
        }

    @staticmethod
    def _flatten_questions(exam_data: dict) -> list[dict]:
        questions = []
        for section in exam_data.get("sections", []):
            questions.extend(section.get("questions", []))
        return questions

    @staticmethod
    def _merge_evaluations(
        teacher_per_q: list[dict],
        resolutions: list[dict],
    ) -> list[dict]:
        """Apply debate resolutions to the Teacher's per-question evaluation."""
        resolution_map = {r["question_id"]: r for r in resolutions}
        merged = []
        for q in teacher_per_q:
            q_id = q.get("question_id")
            resolution = resolution_map.get(q_id)
            if resolution:
                q = {**q, "score": resolution["final_score"]}
                if not q.get("reasoning"):
                    q["reasoning"] = resolution.get("reasoning", q.get("reasoning", ""))
            merged.append(q)
        return merged
```

- [ ] **Step 2: Commit**

```bash
git add master/agents/src/verifier/agent.py
git commit -m "feat(verifier): add VerifierAgent with independent grading + debate merge"
```

---

## Chunk 4: Grading Engine

### Task 12: SymPy Grading Engine

**Files:**
- Create: `master/apps/grading-engine/requirements.txt`
- Create: `master/apps/grading-engine/sympy_grader.py`
- Create: `master/apps/grading-engine/main.py`

- [ ] **Step 1: Write requirements.txt**

```txt
# master/apps/grading-engine/requirements.txt
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
sympy>=1.13.0
pydantic>=2.0.0
```

- [ ] **Step 2: Write sympy_grader.py**

```python
# master/apps/grading-engine/sympy_grader.py
from __future__ import annotations

import logging
from sympy import sympify, simplify, Eq, N
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application

logger = logging.getLogger(__name__)

TRANSFORMATIONS = standard_transformations + (implicit_multiplication_application,)


def verify_math_expression(student_expr: str, correct_expr: str) -> dict:
    """Check if two mathematical expressions are equivalent using SymPy."""
    try:
        student = parse_expr(student_expr, transformations=TRANSFORMATIONS)
        correct = parse_expr(correct_expr, transformations=TRANSFORMATIONS)
        diff = simplify(student - correct)
        is_equal = diff == 0
        return {
            "is_equal": is_equal,
            "student_simplified": str(simplify(student)),
            "correct_simplified": str(simplify(correct)),
            "difference": str(diff),
        }
    except Exception as e:
        logger.error("SymPy verification failed: %s", e)
        return {"is_equal": False, "error": str(e)}


def verify_numeric(student_value: float, correct_value: float, tolerance: float = 1e-6) -> dict:
    """Check if two numeric values are approximately equal."""
    diff = abs(student_value - correct_value)
    is_equal = diff <= tolerance
    return {
        "is_equal": is_equal,
        "student_value": student_value,
        "correct_value": correct_value,
        "difference": diff,
        "tolerance": tolerance,
    }
```

- [ ] **Step 3: Write main.py**

```python
# master/apps/grading-engine/main.py
from fastapi import FastAPI
from pydantic import BaseModel
from sympy_grader import verify_math_expression, verify_numeric

app = FastAPI(title="MASTER Grading Engine", version="0.1.0")


class MathVerifyRequest(BaseModel):
    student_expr: str
    correct_expr: str


class NumericVerifyRequest(BaseModel):
    student_value: float
    correct_value: float
    tolerance: float = 1e-6


@app.get("/health")
async def health():
    return {"status": "ok", "service": "grading-engine"}


@app.post("/verify/math")
async def verify_math(req: MathVerifyRequest):
    return verify_math_expression(req.student_expr, req.correct_expr)


@app.post("/verify/numeric")
async def verify_num(req: NumericVerifyRequest):
    return verify_numeric(req.student_value, req.correct_value, req.tolerance)
```

- [ ] **Step 4: Test locally**

Run:
```bash
cd master/apps/grading-engine
pip install -r requirements.txt
uvicorn main:app --port 8001
```

Test:
```bash
curl -X POST http://localhost:8001/verify/math \
  -H "Content-Type: application/json" \
  -d '{"student_expr": "x**2 + 2*x + 1", "correct_expr": "(x+1)**2"}'
```
Expected: `{"is_equal": true, ...}`

- [ ] **Step 5: Commit**

```bash
git add master/apps/grading-engine/
git commit -m "feat(grading-engine): add SymPy-based math verification service"
```

---

## Summary — What Phúc Delivers

| Day | Deliverable | Notes |
|-----|-------------|-------|
| 1 | `parser/preprocessing.py` + tests | No dependency on common/ |
| 2 | `parser/ocr.py` (PaddleOCR wrapper) | Install PaddleOCR |
| 3 | `parser/extractor.py` + `parser/agent.py` | Needs common/llm_client |
| 4 | `teacher/grading.py` + tests (MC exact match) | — |
| 5 | `teacher/error_analysis.py` + `teacher/agent.py` | Needs LLM for essay |
| 6 | `verifier/discrepancy.py` + tests | — |
| 7 | `verifier/debate.py` + `verifier/agent.py` | — |
| 7 | `grading-engine/` (SymPy service) | Independent |
| 8-9 | Integration with Manager pipeline | Wire into server.py |
