from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Mapping

from exam_scraper.config import Settings
from exam_scraper.core import CrawlService
from exam_scraper.core import normalize_text
from exam_scraper.core import TOANMATH_DOMAIN
from exam_scraper.core import QueryIntentParser, canonicalize_subject, extract_domain

TOOL_NAME = "crawl_toanmath_exams"
TOOL_DESCRIPTION = (
    "Crawl exam PDFs from toanmath.com using explicit filters or a natural-language intent."
)


def _build_start_url(grade: str | None, exam_type: str | None) -> str:
    if not grade or not exam_type:
        return f"https://{TOANMATH_DOMAIN}"

    if exam_type == "thptqg":
        return f"https://{TOANMATH_DOMAIN}/de-thi-thpt-quoc-gia-mon-toan"
    if grade == "thpt":
        return f"https://{TOANMATH_DOMAIN}"

    path = {
        "giua_hk1": "de-thi-giua-hk1-toan",
        "hk1": "de-thi-hk1-toan",
        "giua_hk2": "de-thi-giua-hk2-toan",
        "hk2": "de-thi-hk2-toan",
        "khao_sat": "khao-sat-chat-luong-toan",
        "hsg": "de-thi-hsg-toan",
    }.get(exam_type)

    if not path:
        return f"https://{TOANMATH_DOMAIN}"
    return f"https://{TOANMATH_DOMAIN}/{path}-{grade}"


@dataclass
class CrawlToolInput:
    intent: str | None = None
    start_url: str = f"https://{TOANMATH_DOMAIN}"
    subject: str | None = None
    grade: str | None = None
    exam_type: str | None = None
    limit: int = 5
    force: bool = False


@dataclass
class ResolvedCrawlToolInput:
    start_url: str
    subject: str | None = None
    grade: str | None = None
    exam_type: str | None = None
    limit: int = 5
    notes: list[str] = field(default_factory=list)

    @property
    def allowed_subjects(self) -> set[str] | None:
        if not self.subject:
            return None
        return {self.subject}

    def to_dict(self) -> dict:
        return {
            "start_url": self.start_url,
            "subject": self.subject,
            "grade": self.grade,
            "exam_type": self.exam_type,
            "limit": self.limit,
        }


@dataclass
class CrawlToolResult:
    status: str
    resolved: ResolvedCrawlToolInput
    downloaded_count: int
    documents: list[dict]
    storage_dir: str
    db_path: str
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "tool": TOOL_NAME,
            "status": self.status,
            "resolved": self.resolved.to_dict(),
            "downloaded_count": self.downloaded_count,
            "documents": self.documents,
            "storage_dir": self.storage_dir,
            "db_path": self.db_path,
            "notes": self.notes,
        }


class CrawlTool:
    name = TOOL_NAME
    description = TOOL_DESCRIPTION

    def definition(self) -> dict:
        return get_crawl_tool_definition()

    def run(self, payload: Mapping[str, Any] | CrawlToolInput) -> dict:
        return run_crawl_tool(payload)

    async def arun(self, payload: Mapping[str, Any] | CrawlToolInput) -> dict:
        return await arun_crawl_tool(payload)


def _resolve_from_mapping(mapping: dict[str, list[str]], value: str | None) -> str | None:
    if not value:
        return None

    value_norm = normalize_text(value)
    for canonical, aliases in mapping.items():
        candidates = [canonical, *aliases]
        for candidate in candidates:
            if value_norm == normalize_text(candidate):
                return canonical
    return None


def _normalize_start_url(start_url: str) -> str:
    domain = extract_domain(start_url)
    if domain not in {TOANMATH_DOMAIN, f"www.{TOANMATH_DOMAIN}"}:
        raise ValueError(
            f"`start_url` must belong to {TOANMATH_DOMAIN}, got {start_url!r}."
        )
    return start_url


def _normalize_subject(settings: Settings, subject: str | None) -> str | None:
    if not subject:
        return None

    normalized = canonicalize_subject(subject)
    if normalized != "unknown":
        return normalized

    normalized = _resolve_from_mapping(settings.detectors.intent.subjects, subject)
    if normalized:
        return normalized
    raise ValueError(f"Unsupported subject filter: {subject!r}")


def _normalize_grade(settings: Settings, grade: str | None) -> str | None:
    if not grade:
        return None

    normalized = _resolve_from_mapping(settings.detectors.intent.grades, grade)
    if normalized:
        return normalized
    raise ValueError(f"Unsupported grade filter: {grade!r}")


def _normalize_exam_type(settings: Settings, exam_type: str | None) -> str | None:
    if not exam_type:
        return None

    normalized = _resolve_from_mapping(settings.detectors.intent.exam_types, exam_type)
    if normalized:
        return normalized
    raise ValueError(f"Unsupported exam type filter: {exam_type!r}")


def _normalize_limit(limit: int) -> int:
    if limit <= 0:
        raise ValueError(f"`limit` must be greater than 0, got {limit}.")
    return limit


def build_crawl_tool_input(payload: Mapping[str, Any] | CrawlToolInput) -> CrawlToolInput:
    if isinstance(payload, CrawlToolInput):
        return payload
    return CrawlToolInput(
        intent=payload.get("intent") or payload.get("query") or payload.get("task"),
        start_url=payload.get("start_url", f"https://{TOANMATH_DOMAIN}"),
        subject=payload.get("subject"),
        grade=payload.get("grade"),
        exam_type=payload.get("exam_type"),
        limit=int(payload.get("limit", 5)),
        force=bool(payload.get("force", False)),
    )


def resolve_crawl_tool_input(
    payload: Mapping[str, Any] | CrawlToolInput,
    settings: Settings | None = None,
) -> ResolvedCrawlToolInput:
    settings = settings or Settings.from_yaml()
    request = build_crawl_tool_input(payload)
    parser = QueryIntentParser(settings.detectors.intent)
    intent = parser.parse(request.intent)
    notes: list[str] = []

    explicit_subject = _normalize_subject(settings, request.subject)
    intent_subject = _normalize_subject(settings, intent.subject) if intent.subject else None
    if explicit_subject and intent_subject and explicit_subject != intent_subject:
        notes.append(
            f"Ignored intent subject {intent_subject!r} in favor of explicit subject."
        )
    subject = explicit_subject or intent_subject

    explicit_grade = _normalize_grade(settings, request.grade)
    intent_grade = _normalize_grade(settings, intent.grade) if intent.grade else None
    if explicit_grade and intent_grade and explicit_grade != intent_grade:
        notes.append(f"Ignored intent grade {intent_grade!r} in favor of explicit grade.")
    grade = explicit_grade or intent_grade

    explicit_exam_type = _normalize_exam_type(settings, request.exam_type)
    intent_exam_type = (
        _normalize_exam_type(settings, intent.exam_type) if intent.exam_type else None
    )
    if explicit_exam_type and intent_exam_type and explicit_exam_type != intent_exam_type:
        notes.append(
            f"Ignored intent exam type {intent_exam_type!r} in favor of explicit exam type."
        )
    exam_type = explicit_exam_type or intent_exam_type
    start_url = request.start_url
    if start_url.rstrip("/") == f"https://{TOANMATH_DOMAIN}" and grade and exam_type:
        start_url = _build_start_url(grade, exam_type)

    return ResolvedCrawlToolInput(
        start_url=_normalize_start_url(start_url),
        subject=subject,
        grade=grade,
        exam_type=exam_type,
        limit=_normalize_limit(request.limit),
        notes=notes,
    )


async def arun_crawl_tool(
    payload: Mapping[str, Any] | CrawlToolInput,
    settings: Settings | None = None,
) -> dict:
    settings = settings or Settings.from_yaml()
    request = build_crawl_tool_input(payload)
    resolved = resolve_crawl_tool_input(request, settings=settings)
    service = CrawlService(settings)

    if request.force:
        await service.clear_cache()

    summary = await service.run_with_summary(
        start_url=resolved.start_url,
        limit=resolved.limit,
        allowed_subjects=resolved.allowed_subjects,
        grade_filter=resolved.grade,
        exam_type_filter=resolved.exam_type,
    )
    result = CrawlToolResult(
        status="success",
        resolved=resolved,
        downloaded_count=summary.downloaded_count,
        documents=[doc.to_dict() for doc in summary.documents],
        storage_dir=str(settings.storage_path.resolve()),
        db_path=str(settings.db_path.resolve()),
        notes=list(resolved.notes),
    )
    return result.to_dict()


def run_crawl_tool(
    payload: Mapping[str, Any] | CrawlToolInput,
    settings: Settings | None = None,
) -> dict:
    return asyncio.run(arun_crawl_tool(payload, settings=settings))


def crawl_toanmath_by_tags(
    grade: str,
    exam_type: str,
    limit: int = 5,
    settings: Settings | None = None,
) -> dict:
    """Crawl ToanMath exam PDFs using only grade, exam type, and limit.

    This is the preferred simple function for an AI Agent. The Agent should only
    decide these tags:

    - grade: one of "10", "11", "12", or "thpt".
    - exam_type: one of "giua_hk1", "hk1", "giua_hk2", "hk2",
      "khao_sat", "hsg", or "thptqg". Common aliases like "gk1", "ck1",
      "gk2", "ck2", "kscl", "hoc sinh gioi", and "tnthpt" are accepted.
    - limit: maximum number of PDFs to download. It is an upper bound, not a
      guarantee that exactly this many files will be downloaded.

    The function always crawls only toanmath.com. It automatically chooses a
    ToanMath start URL from grade and exam_type, then runs the same crawler
    used by the CLI. The returned dict contains status, resolved filters,
    downloaded_count, documents, storage_dir, db_path, and notes.

    Example:
        result = crawl_toanmath_by_tags(grade="12", exam_type="hk1", limit=5)
    """
    settings = settings or Settings.from_yaml()
    normalized_grade = _normalize_grade(settings, grade)
    normalized_exam_type = _normalize_exam_type(settings, exam_type)
    start_url = _build_start_url(normalized_grade, normalized_exam_type)

    return run_crawl_tool(
        {
            "start_url": start_url,
            "grade": normalized_grade,
            "exam_type": normalized_exam_type,
            "limit": limit,
        },
        settings=settings,
    )


def get_crawl_tool_definition() -> dict:
    return {
        "name": TOOL_NAME,
        "description": TOOL_DESCRIPTION,
        "input_schema": {
            "type": "object",
            "properties": {
                "intent": {
                    "type": "string",
                    "description": "Natural-language request like 'lay de gk1 mon toan lop 11'.",
                },
                "start_url": {
                    "type": "string",
                    "description": "Optional ToanMath URL to start crawling from.",
                },
                "subject": {
                    "type": "string",
                    "description": "Explicit subject override.",
                },
                "grade": {
                    "type": "string",
                    "description": "Explicit grade override: 10, 11, 12, thpt.",
                },
                "exam_type": {
                    "type": "string",
                    "description": (
                        "Explicit exam type override: gk1, hk1, gk2, hk2, "
                        "khao_sat, hsg, thptqg."
                    ),
                },
                "limit": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "Maximum PDFs to download.",
                },
                "force": {
                    "type": "boolean",
                    "description": "Clear dedup cache before crawling.",
                },
            },
            "additionalProperties": False,
        },
    }


def get_crawl_tool() -> CrawlTool:
    return CrawlTool()
