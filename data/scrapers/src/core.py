from __future__ import annotations

import hashlib
import re
import shutil
import unicodedata
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, quote, unquote, urldefrag, urljoin, urlparse, urlunparse
from uuid import uuid4

import aiosqlite
import structlog
from bs4 import BeautifulSoup
from playwright.async_api import (
    APIResponse,
    Browser,
    BrowserContext,
    Error as PlaywrightError,
    Page,
    async_playwright,
)

from exam_scraper.config import DetectorConfig, IntentKeywordConfig, Settings
from exam_scraper.pdf_splitter import split_pdf_to_pdf


logger = structlog.get_logger()


# ---- url_utils.py ----

def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path.rstrip("/") or "/"
    unquoted_path = unquote(path)
    quoted_path = quote(unquoted_path)
    normalized = urlunparse((
        parsed.scheme.lower(),
        parsed.netloc.lower(),
        quoted_path,
        "",
        "",
        "",
    ))
    return normalized


def url_hash(url: str) -> str:
    return hashlib.sha256(normalize_url(url).encode()).hexdigest()


def extract_domain(url: str) -> str:
    return urlparse(url).netloc.lower()


def is_pdf_url(url: str) -> bool:
    path = urlparse(url).path.lower()
    return path.endswith(".pdf")


def resolve_url(base: str, relative: str) -> str:
    return urljoin(base, relative)


_YEAR_PATTERN = re.compile(r"(?:20[1-3]\d)")


def extract_year(text: str) -> int | None:
    matches = _YEAR_PATTERN.findall(text)
    if not matches:
        return None
    years = [int(y) for y in matches if 2010 <= int(y) <= 2030]
    return max(years) if years else None


_GDRIVE_PATTERNS = [
    re.compile(r"drive\.google\.com/file/d/([a-zA-Z0-9_-]+)"),
    re.compile(r"drive\.google\.com/open\?id=([a-zA-Z0-9_-]+)"),
    re.compile(r"docs\.google\.com/.*?/d/([a-zA-Z0-9_-]+)"),
]


def extract_gdrive_id(url: str) -> str | None:
    for pattern in _GDRIVE_PATTERNS:
        match = pattern.search(url)
        if match:
            return match.group(1)
    return None


def gdrive_direct_url(file_id: str) -> str:
    return f"https://drive.google.com/uc?export=download&id={file_id}"

def extract_school(title: str) -> str:
    match = re.search(r'(?i)(trường|sở|chuyên|thpt)\s+([^,\-\.\(|]+)', title)
    if match:
        name = str(match.group(0)).strip()
        # safe slice with string cast
        s_name = str(name)
        if len(s_name) > 40:
            return s_name[:40]
        return s_name
    return ""

def _remove_accents(input_str: str) -> str:
    nfkd_form = unicodedata.normalize("NFKD", input_str)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])


def canonicalize_subject(subject: str | None) -> str:
    if not subject:
        return "unknown"

    normalized = _remove_accents(subject).lower().replace("-", "_").replace(" ", "_")
    normalized = re.sub(r"[^a-z0-9_]", "", normalized)
    normalized = re.sub(r"_+", "_", normalized).strip("_")

    alias_map = {
        "toan": "toan",
        "van": "van",
        "ngu_van": "van",
        "nguvan": "van",
        "anh": "anh",
        "tieng_anh": "anh",
        "tienganh": "anh",
        "ngoai_ngu": "anh",
        "ngoaingu": "anh",
        "ly": "ly",
        "vat_ly": "ly",
        "vatly": "ly",
        "vat_li": "ly",
        "vatli": "ly",
        "hoa": "hoa",
        "hoa_hoc": "hoa",
        "hoahoc": "hoa",
        "sinh": "sinh",
        "sinh_hoc": "sinh",
        "sinhhoc": "sinh",
        "su": "su",
        "lich_su": "su",
        "lichsu": "su",
        "dia": "dia",
        "dia_ly": "dia",
        "dialy": "dia",
        "gdcd": "gdcd",
        "gdktpl": "gdktpl",
        "kinh_te": "gdktpl",
        "kinhte": "gdktpl",
        "phap_luat": "gdktpl",
        "phapluat": "gdktpl",
        "kinh_te_phap_luat": "gdktpl",
        "kinhtephapluat": "gdktpl",
        "tin": "tin",
        "tin_hoc": "tin",
        "tinhoc": "tin",
        "cong_nghe": "cong_nghe",
        "congnghe": "cong_nghe",
    }
    return alias_map.get(normalized, "unknown")


def extract_subject(title: str, url: str) -> str:
    combined = (_remove_accents(title) + " " + _remove_accents(url)).lower()
    
    if re.search(r'\btoan\b', combined):
        return "toan"
    if re.search(r'\b(van|ngu-van|ngu van)\b', combined):
        return "van"
    if re.search(r'\b(anh|tieng-anh|tieng anh|ngoai-ngu|ngoai ngu)\b', combined):
        return "anh"
    if re.search(r'\b(ly|vat-ly|vat ly|vat-li|vat li)\b', combined):
        return "ly"
    if re.search(r'\bhoa\b', combined):
        return "hoa"
    if re.search(r'\bsinh\b', combined):
        return "sinh"
    if re.search(r'\b(su|lich-su|lich su)\b', combined):
        return "su"
    if re.search(r'\bdia\b', combined):
        return "dia"
    if re.search(r'\b(gdktpl|kinh-te|kinh te|phap-luat|phap luat|gdcd)\b', combined):
        return "gdktpl"
        
    return "unknown"


# ---- paths.py ----

GRADE_DIRS = {
    "10": "lop-10",
    "11": "lop-11",
    "12": "lop-12",
    "thpt": "thpt",
}


def sanitize_filename(name: str) -> str:
    name = name.replace("Đ", "D").replace("đ", "d")
    name = unicodedata.normalize("NFKD", name)
    name = "".join(ch for ch in name if not unicodedata.combining(ch))
    name = re.sub(r'[<>:"/\\|?*]', "_", name)
    name = re.sub(r"[^A-Za-z0-9._-]", "_", name)
    name = re.sub(r"\s+", "_", name)
    name = re.sub(r"_+", "_", name)
    return name.strip("_").lower()


def normalize_grade_dir(grade: str | None) -> str | None:
    if not grade:
        return None
    return GRADE_DIRS.get(str(grade).strip().lower())


def build_pdf_path(
    storage_dir: Path,
    subject: str | None,
    grade: str | None,
) -> Path:
    canonical_subject = canonicalize_subject(subject)
    grade_dir = normalize_grade_dir(grade)
    if canonical_subject != "unknown" and grade_dir:
        path = storage_dir / canonical_subject / grade_dir
    else:
        path = storage_dir / "others"
    path.mkdir(parents=True, exist_ok=True)
    return path


def build_pdf_filename(
    grade: str | None,
    subject: str | None,
    exam_type: str | None,
    source: str,
    school: str = "",
    year: int | None = None,
    suffix: str = "",
) -> str:
    source_clean = source.replace(".", "").replace("www", "")
    parts: list[str] = []
    canonical_subject = canonicalize_subject(subject)
    grade_dir = normalize_grade_dir(grade)
    if canonical_subject != "unknown":
        parts.append(canonical_subject)
    if grade_dir:
        parts.append(grade_dir)
    if exam_type:
        parts.append(str(exam_type))
    if school:
        parts.append(school)
    if year:
        parts.append(str(year))
    parts.append(source_clean)
    if suffix:
        parts.append(suffix)
    return sanitize_filename("_".join(parts)) + ".pdf"


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def ensure_unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    counter = 1
    while True:
        new_path = parent / f"{stem}_{counter}{suffix}"
        if not new_path.exists():
            return new_path
        counter += 1


# ---- metadata.py ----

TOANMATH_DOMAIN = "toanmath.com"

SCHEMA = """
CREATE TABLE IF NOT EXISTS crawled_urls (
    url_hash TEXT PRIMARY KEY,
    url TEXT NOT NULL,
    domain TEXT NOT NULL,
    has_pdf INTEGER DEFAULT 0,
    crawled_at TEXT DEFAULT (datetime('now')),
    ttl_days INTEGER DEFAULT 7
);

CREATE INDEX IF NOT EXISTS idx_crawled_domain ON crawled_urls(domain);

CREATE TABLE IF NOT EXISTS exam_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_url TEXT NOT NULL,
    source_domain TEXT NOT NULL,
    pdf_url TEXT NOT NULL,
    local_path TEXT NOT NULL,
    file_hash TEXT UNIQUE,
    file_size_bytes INTEGER,
    title TEXT,
    grade TEXT,
    subject TEXT,
    exam_type TEXT,
    year INTEGER,
    province TEXT,
    parse_status TEXT DEFAULT 'pending',
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_exam_year ON exam_documents(year DESC);
CREATE INDEX IF NOT EXISTS idx_exam_parse ON exam_documents(parse_status);
CREATE INDEX IF NOT EXISTS idx_exam_grade ON exam_documents(grade, subject);
"""


@dataclass
class ExamDocument:
    source_url: str
    source_domain: str
    pdf_url: str
    local_path: str
    file_hash: str = ""
    file_size_bytes: int = 0
    title: str = ""
    grade: str = ""
    subject: str = ""
    exam_type: str = ""
    year: int | None = None
    province: str = ""
    parse_status: str = "pending"
    id: int | None = None

    def to_dict(self) -> dict:
        return {
            "source_url": self.source_url,
            "source_domain": self.source_domain,
            "pdf_url": self.pdf_url,
            "local_path": self.local_path,
            "file_hash": self.file_hash,
            "file_size_bytes": self.file_size_bytes,
            "title": self.title,
            "grade": self.grade,
            "subject": self.subject,
            "exam_type": self.exam_type,
            "year": self.year,
            "province": self.province,
            "parse_status": self.parse_status,
        }


@dataclass
class ExamInfo:
    title: str = ""
    grade: str = ""
    subject: str = ""
    exam_type: str = ""
    year: int | None = None
    province: str = ""
    pdf_urls: list[str] = field(default_factory=list)


async def get_db(db_path: Path) -> aiosqlite.Connection:
    db = await aiosqlite.connect(str(db_path))
    db.row_factory = aiosqlite.Row
    await db.executescript(SCHEMA)
    await db.commit()
    return db


# ---- dedup.py ----

class DedupCache:
    def __init__(self, db: aiosqlite.Connection, ttl_days: int = 7):
        self._db = db
        self._ttl_days = ttl_days

    async def is_crawled(self, url: str) -> bool:
        h = url_hash(url)
        cursor = await self._db.execute(
            "SELECT crawled_at, ttl_days FROM crawled_urls WHERE url_hash = ?",
            (h,),
        )
        row = await cursor.fetchone()
        if row is None:
            return False
        crawled_at = datetime.fromisoformat(row["crawled_at"])
        ttl = timedelta(days=row["ttl_days"])
        return datetime.utcnow() - crawled_at < ttl

    async def mark_crawled(
        self, url: str, has_pdf: bool = False, commit: bool = True
    ) -> None:
        h = url_hash(url)
        await self._db.execute(
            """INSERT OR REPLACE INTO crawled_urls
               (url_hash, url, domain, has_pdf, ttl_days)
               VALUES (?, ?, ?, ?, ?)""",
            (h, normalize_url(url), extract_domain(url), int(has_pdf), self._ttl_days),
        )
        if commit:
            await self._db.commit()

    async def clear(self, domain: str) -> int:
        cursor = await self._db.execute(
            "DELETE FROM crawled_urls WHERE domain = ?", (domain,)
        )
        await self._db.commit()
        return cursor.rowcount


# ---- download_detector.py ----

def normalize_text(value: str) -> str:
    nfkd = unicodedata.normalize("NFKD", value or "")
    no_accent = "".join(ch for ch in nfkd if not unicodedata.combining(ch))
    lowered = no_accent.lower()
    lowered = lowered.replace("-", " ").replace("_", " ")
    lowered = re.sub(r"\s+", " ", lowered).strip()
    return lowered


def contains_keyword(text: str, keyword: str) -> bool:
    text_norm = normalize_text(text)
    kw_norm = normalize_text(keyword)
    if not kw_norm:
        return False
    pattern = r"(?<!\w)" + re.escape(kw_norm).replace(r"\ ", r"[\s_-]+") + r"(?!\w)"
    return re.search(pattern, text_norm) is not None


@dataclass
class DownloadCandidate:
    index: int
    text: str = ""
    href: str = ""
    aria_label: str = ""
    title: str = ""
    class_name: str = ""
    element_id: str = ""
    nearby_text: str = ""
    score: float = 0.0

    @classmethod
    def from_dict(cls, index: int, data: dict[str, Any]) -> DownloadCandidate:
        return cls(
            index=index,
            text=str(data.get("text") or ""),
            href=str(data.get("href") or ""),
            aria_label=str(data.get("aria_label") or ""),
            title=str(data.get("title") or ""),
            class_name=str(data.get("class_name") or ""),
            element_id=str(data.get("element_id") or ""),
            nearby_text=str(data.get("nearby_text") or ""),
        )


class DownloadTargetDetector:
    def __init__(self, config: DetectorConfig):
        self._config = config
        self._positive = [normalize_text(k) for k in config.download_keywords.positive if k]
        self._negative = [normalize_text(k) for k in config.download_keywords.negative if k]
        self._weights = config.download_keywords.weights

    def score(self, candidate: DownloadCandidate) -> float:
        score = 0.0
        fields = {
            "text": candidate.text,
            "href": candidate.href,
            "aria_label": candidate.aria_label,
            "title": candidate.title,
            "class_name": candidate.class_name,
            "element_id": candidate.element_id,
            "nearby_text": candidate.nearby_text,
        }

        for field, value in fields.items():
            weight = float(self._weights.get(field, 1.0))
            if not value:
                continue
            for keyword in self._positive:
                if contains_keyword(value, keyword):
                    score += weight
            for keyword in self._negative:
                if contains_keyword(value, keyword):
                    score -= weight * 2

        href_norm = normalize_text(candidate.href)
        if ".pdf" in href_norm:
            score += 6.0
        if "drive.google.com" in href_norm:
            score += 3.0
        if "javascript:" in href_norm and score <= 0:
            score -= 1.0

        candidate.score = score
        return score

    def rank(self, raw_candidates: list[dict[str, Any]]) -> list[DownloadCandidate]:
        candidates = [
            DownloadCandidate.from_dict(idx, item)
            for idx, item in enumerate(raw_candidates)
        ]
        for candidate in candidates:
            self.score(candidate)
        candidates.sort(key=lambda item: item.score, reverse=True)
        return candidates


# ---- parser.py ----

class ToanMathParser:
    domain = "toanmath.com"

    def parse_listing_page(self, html: str, url: str) -> list[str]:
        soup = BeautifulSoup(html, "html.parser")
        urls: list[str] = []
        seen: set[str] = set()

        for tag in soup.find_all("a", href=True):
            href = tag["href"].strip()
            full_url = resolve_url(url, href)
            if full_url in seen:
                continue
            seen.add(full_url)
            urls.append(full_url)

        return urls

    def parse_detail_page(self, html: str, url: str) -> ExamInfo:
        soup = BeautifulSoup(html, "html.parser")

        title_tag = soup.find("h1") or soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else ""
        search_str = normalize_text(f"{title} {unquote(url)}")

        info = ExamInfo(
            title=title,
            subject=extract_subject(title, url),
            pdf_urls=self._extract_pdf_urls(html, url),
            year=extract_year(title) or extract_year(url),
            province=extract_school(title),
        )

        if self._contains_grade(search_str, "10"):
            info.grade = "10"
        elif self._contains_grade(search_str, "11"):
            info.grade = "11"
        elif self._contains_grade(search_str, "12"):
            info.grade = "12"
        elif "thpt" in search_str or "tot nghiep" in search_str:
            info.grade = "thpt"

        if any(
            token in search_str
            for token in ("giua hk1", "giua ky 1", "giua ki 1", "giua hoc ky 1", "giua hoc ki 1")
        ):
            info.exam_type = "giua_hk1"
        elif any(
            token in search_str
            for token in ("hk1", "hoc ky 1", "hoc ki 1", "ky 1", "ki 1", "cuoi ky 1", "cuoi ki 1")
        ):
            info.exam_type = "hk1"
        elif any(
            token in search_str
            for token in ("giua hk2", "giua ky 2", "giua ki 2", "giua hoc ky 2", "giua hoc ki 2")
        ):
            info.exam_type = "giua_hk2"
        elif any(
            token in search_str
            for token in ("hk2", "hoc ky 2", "hoc ki 2", "ky 2", "ki 2", "cuoi ky 2", "cuoi ki 2")
        ):
            info.exam_type = "hk2"
        elif any(
            token in search_str
            for token in ("khao sat", "khao sat chat luong", "kscl")
        ):
            info.exam_type = "khao_sat"
        elif any(
            token in search_str
            for token in ("hsg", "hoc sinh gioi", "de thi hsg")
        ):
            info.exam_type = "hsg"
        elif any(
            token in search_str
            for token in (
                "thptqg",
                "thpt qg",
                "tnthpt",
                "tot nghiep thpt",
                "thi tot nghiep thpt",
                "thi thpt quoc gia",
            )
        ):
            info.exam_type = "thptqg"
        elif "de-cuong" in search_str or "de cuong" in search_str:
            info.exam_type = "de_cuong"
        elif "thi-thu" in search_str or "thi thu" in search_str:
            info.exam_type = "thi_thu"

        return info

    def matches(self, url: str) -> bool:
        return extract_domain(url) in {self.domain, f"www.{self.domain}"}

    @staticmethod
    def _contains_grade(text: str, grade: str) -> bool:
        return re.search(rf"(lop|khoi)[-_ ]*{grade}|\b{grade}\b", text) is not None

    @staticmethod
    def _extract_pdf_urls(html: str, base_url: str) -> list[str]:
        soup = BeautifulSoup(html, "html.parser")
        urls: list[str] = []
        seen: set[str] = set()

        def _add(url: str) -> None:
            if url and url not in seen:
                seen.add(url)
                urls.append(url)

        for tag in soup.find_all("a", href=True):
            href = tag["href"].strip()
            full_url = resolve_url(base_url, href)
            gid = extract_gdrive_id(full_url)
            if gid:
                _add(gdrive_direct_url(gid))
                continue
            if is_pdf_url(full_url) or ".pdf" in href.lower() or "download" in href.lower():
                _add(full_url)

        for tag in soup.find_all(("iframe", "embed"), src=True):
            src = tag["src"].strip()
            full_url = resolve_url(base_url, src)
            gid = extract_gdrive_id(full_url)
            if gid:
                _add(gdrive_direct_url(gid))
            elif is_pdf_url(full_url):
                _add(full_url)

        return urls


# ---- transaction.py ----

class CrawlTransaction:
    def __init__(self, db: aiosqlite.Connection, temp_dir: Path):
        self._db = db
        self.temp_dir = temp_dir
        self._moved_files: list[Path] = []

    async def begin(self) -> None:
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        await self._db.execute("BEGIN")

    def build_temp_path(self, filename: str) -> Path:
        return self.temp_dir / f"{filename}.part"

    def register_final_file(self, path: Path) -> None:
        self._moved_files.append(path)

    async def commit(self) -> None:
        await self._db.commit()
        self._cleanup_temp()

    async def rollback(self) -> None:
        await self._db.rollback()
        for path in self._moved_files:
            path.unlink(missing_ok=True)
        self._cleanup_temp()

    def _cleanup_temp(self) -> None:
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)


# ---- playwright_client.py ----

@dataclass
class DownloadResult:
    size: int
    status_code: int
    headers: dict[str, str]


@dataclass
class CapturedPdfUrl:
    url: str
    content_type: str = ""
    content_disposition: str = ""
    source: str = ""

    def has_network_pdf_signal(self) -> bool:
        return _is_pdf_like(self.url, self.content_type, self.content_disposition)


_STATIC_ASSET_EXTENSIONS = {
    ".svg",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".ico",
    ".css",
    ".js",
    ".map",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
}


_JUNK_URL_HOSTS = (
    "doubleclick.net",
    "googlesyndication.com",
    "googleadservices.com",
    "googleads.g.doubleclick.net",
    "adtrafficquality.google",
    "google-analytics.com",
    "googletagmanager.com",
    "googletagservices.com",
    "facebook.com",
    "facebook.net",
)

_JUNK_URL_PATH_TOKENS = (
    "/recaptcha/",
    "/pagead/",
    "/sodar/",
    "/ads?",
    "/ad_status",
)


def _normalize_capture_url(url: str) -> str:
    if not url:
        return ""
    clean, _fragment = urldefrag(url.strip())
    return clean


def _is_junk_url(url: str) -> bool:
    if not url or url in {"about:blank", "about:srcdoc"}:
        return True
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    full = url.lower()
    if parsed.scheme and parsed.scheme not in {"http", "https"}:
        return True
    if any(host == item or host.endswith(f".{item}") for item in _JUNK_URL_HOSTS):
        return True
    return any(token in full for token in _JUNK_URL_PATH_TOKENS)


def _is_static_asset_url(url: str) -> bool:
    path = urlparse(url).path.lower()
    return any(path.endswith(ext) for ext in _STATIC_ASSET_EXTENSIONS)


def _extract_embedded_pdf_url(url: str) -> str | None:
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    for key in ("file", "url", "src", "download"):
        for value in query.get(key, []):
            unquoted = unquote(value).strip()
            if _is_pdf_like(unquoted):
                return _normalize_capture_url(unquoted)
    return None


def _is_pdf_like(
    url: str, content_type: str | None = None, content_disposition: str | None = None
) -> bool:
    parsed = urlparse(url)
    path = parsed.path.lower()
    query = parse_qs(parsed.query)
    ct_norm = normalize_text(content_type or "")
    cd_norm = normalize_text(content_disposition or "")
    if path.endswith(".pdf"):
        return True
    for key in ("file", "url", "src", "download"):
        for value in query.get(key, []):
            value_norm = normalize_text(unquote(value))
            if ".pdf" in value_norm:
                return True
    if "application/pdf" in ct_norm:
        return True
    if "filename=" in cd_norm and ".pdf" in cd_norm:
        return True
    return False


class PlaywrightCrawlerClient:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._playwright = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None
        self._clicked_history: deque[str] = deque()

    async def _ensure_context(self) -> BrowserContext:
        if self._context is not None:
            return self._context

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=self._settings.playwright.headless
        )
        self._context = await self._browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="vi-VN",
            accept_downloads=True,
        )
        logger.info("playwright_context_ready")
        return self._context

    async def _ensure_page(self) -> Page:
        if self._page is not None and not self._page.is_closed():
            return self._page
        context = await self._ensure_context()
        self._page = await context.new_page()
        return self._page

    @property
    def clicked_history(self) -> list[str]:
        return list(self._clicked_history)

    def _remember_url(self, url: str) -> None:
        if not url:
            return
        normalized = normalize_url(url)
        if self._clicked_history and self._clicked_history[-1] == normalized:
            return
        self._clicked_history.append(normalized)

    @staticmethod
    def _same_url(left: str, right: str) -> bool:
        if not left or not right:
            return False
        return normalize_url(left) == normalize_url(right)

    async def _scroll_to_bottom(self, page: Page) -> None:
        try:
            await page.evaluate(
                """() => {
                    const target = document.scrollingElement || document.documentElement || document.body;
                    if (!target) return;
                    window.scrollTo(0, target.scrollHeight);
                    target.scrollTop = target.scrollHeight;
                }"""
            )
        except PlaywrightError:
            return

    async def goto(self, url: str) -> Page:
        page = await self._ensure_page()
        if not self._same_url(str(page.url or ""), url):
            await page.goto(
                url,
                wait_until="networkidle",
                timeout=self._settings.playwright.timeout,
            )
        await self._scroll_to_bottom(page)
        self._remember_url(str(page.url or url))
        return page

    async def go_back_to(self, parent_url: str | None) -> None:
        if not parent_url:
            return

        page = await self._ensure_page()
        if self._same_url(str(page.url or ""), parent_url):
            return

        try:
            response = await page.go_back(
                wait_until="networkidle",
                timeout=self._settings.playwright.timeout,
            )
            if response is None or not self._same_url(str(page.url or ""), parent_url):
                await page.goto(
                    parent_url,
                    wait_until="networkidle",
                    timeout=self._settings.playwright.timeout,
                )
        except PlaywrightError:
            await page.goto(
                parent_url,
                wait_until="networkidle",
                timeout=self._settings.playwright.timeout,
            )

        self._remember_url(str(page.url or parent_url))

    async def detect_pdf_urls(
        self,
        detail_url: str,
        detector: DownloadTargetDetector,
    ) -> tuple[str, list[CapturedPdfUrl]]:
        page = await self.goto(detail_url)
        captured: list[CapturedPdfUrl] = []
        seen: set[str] = set()

        def _capture(
            url: str,
            content_type: str = "",
            content_disposition: str = "",
            source: str = "",
        ) -> None:
            normalized = _normalize_capture_url(url)
            if (
                not normalized
                or normalized in seen
                or _is_junk_url(normalized)
                or _is_static_asset_url(normalized)
            ):
                return
            seen.add(normalized)
            captured.append(
                CapturedPdfUrl(
                    url=normalized,
                    content_type=content_type or "",
                    content_disposition=content_disposition or "",
                    source=source,
                )
            )
            embedded = _extract_embedded_pdf_url(normalized)
            if embedded and embedded not in seen and not _is_static_asset_url(embedded):
                seen.add(embedded)
                captured.append(
                    CapturedPdfUrl(
                        url=embedded,
                        content_type="application/pdf",
                        content_disposition="",
                        source=f"{source}_embedded",
                    )
                )

        def _on_response(response) -> None:
            headers = {k.lower(): v for k, v in response.headers.items()}
            url = str(response.url or "")
            ctype = headers.get("content-type", "")
            cdisp = headers.get("content-disposition", "")
            if _is_pdf_like(url, ctype, cdisp):
                _capture(url, ctype, cdisp, "response")

        def _on_request(request) -> None:
            url = str(request.url or "")
            if _is_pdf_like(url):
                _capture(url, source="request")

        page.on("response", _on_response)
        page.on("request", _on_request)

        try:
            html = await page.content()

            for frame in page.frames:
                if frame == page.main_frame:
                    continue
                if frame.url:
                    _capture(str(frame.url), source="frame_url")

            # Known PDFJS/WonderPlugin viewer: click download button inside iframe if available.
            for frame in page.frames:
                if frame == page.main_frame:
                    continue
                frame_url = str(frame.url or "").lower()
                if "viewer" not in frame_url and "pdfjs" not in frame_url:
                    continue
                try:
                    button = frame.locator("#download")
                    if await button.count() > 0:
                        await button.first.click(timeout=1500, force=True)
                        await page.wait_for_timeout(self._settings.detectors.network_wait_ms)
                except PlaywrightError:
                    continue

            raw_candidates = await page.eval_on_selector_all(
                "a,button,[role='button'],[onclick],[data-href]",
                """(elements) => elements.slice(0, 300).map((el) => ({
                    text: (el.innerText || el.textContent || "").trim().slice(0, 240),
                    href: (el.getAttribute("href") || el.getAttribute("data-href") || "").trim(),
                    aria_label: (el.getAttribute("aria-label") || "").trim(),
                    title: (el.getAttribute("title") || "").trim(),
                    class_name: String(el.className || "").trim(),
                    element_id: (el.id || "").trim(),
                    nearby_text: ((el.parentElement && el.parentElement.innerText) || "").trim().slice(0, 240)
                }))""",
            )
            ranked = detector.rank(raw_candidates)
            handles = await page.query_selector_all(
                "a,button,[role='button'],[onclick],[data-href]"
            )

            # Direct href candidates should be considered before click.
            for candidate in ranked[: self._settings.detectors.max_click_attempts]:
                href = candidate.href.strip()
                if not href:
                    continue
                absolute = resolve_url(detail_url, href)
                gid = extract_gdrive_id(absolute)
                if gid:
                    absolute = gdrive_direct_url(gid)
                if gid or _is_pdf_like(absolute):
                    _capture(absolute, source="href")

            if not captured:
                for candidate in ranked[: self._settings.detectors.max_click_attempts]:
                    if candidate.score <= 0:
                        continue
                    if candidate.href.strip():
                        continue
                    if candidate.index >= len(handles):
                        continue
                    handle = handles[candidate.index]
                    before_count = len(captured)

                    try:
                        async with page.expect_download(
                            timeout=self._settings.detectors.network_wait_ms
                        ) as download_info:
                            await handle.click(timeout=2000, force=True)
                        download = await download_info.value
                        download_url = str(download.url or "")
                        if download_url:
                            _capture(download_url, source="download_event")
                    except PlaywrightError:
                        continue

                    current_url = str(page.url or "")
                    if _is_pdf_like(current_url):
                        _capture(current_url, source="post_click_url")
                    if len(captured) > before_count:
                        break

            source_priority = {
                "download_event": 100,
                "response": 90,
                "request_embedded": 85,
                "response_embedded": 85,
                "frame_url_embedded": 83,
                "href": 70,
                "request": 50,
                "post_click_url": 40,
                "frame_url": 30,
            }

            def _priority(item: CapturedPdfUrl) -> int:
                base = source_priority.get(item.source, 10)
                if urlparse(item.url).path.lower().endswith(".pdf"):
                    base += 20
                return base

            captured.sort(key=_priority, reverse=True)
            return html, captured
        finally:
            page.remove_listener("response", _on_response)
            page.remove_listener("request", _on_request)

    async def head_file_size(self, url: str) -> int | None:
        context = await self._ensure_context()
        response = await context.request.fetch(
            url,
            method="HEAD",
            timeout=self._settings.playwright.timeout,
        )
        return self._extract_content_length(response)

    async def fetch_file_header(self, url: str, max_bytes: int = 65536) -> bytes | None:
        context = await self._ensure_context()
        response = await context.request.fetch(
            url,
            method="GET",
            headers={"Range": f"bytes=0-{max_bytes - 1}"},
            timeout=self._settings.playwright.timeout,
        )
        if response.status >= 400:
            return None
        body = await response.body()
        return body[:max_bytes] if body else None

    async def download_file(
        self,
        url: str,
        dest: Path,
        referer: str | None = None,
    ) -> DownloadResult:
        context = await self._ensure_context()
        headers: dict[str, str] = {}
        if referer:
            headers["Referer"] = referer

        response = await context.request.fetch(
            url,
            method="GET",
            headers=headers,
            timeout=self._settings.playwright.timeout,
        )
        if response.status >= 400:
            raise ValueError(f"Download request failed with status {response.status}")

        body = await response.body()
        if body is None:
            raise ValueError("Empty response body")
        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, "wb") as f:
            f.write(body)
        normalized_headers = {k.lower(): v for k, v in response.headers.items()}
        return DownloadResult(
            size=len(body),
            status_code=response.status,
            headers=normalized_headers,
        )

    @staticmethod
    def _extract_content_length(response: APIResponse) -> int | None:
        if response.status >= 400:
            return None
        for key, value in response.headers.items():
            if key.lower() == "content-length" and str(value).isdigit():
                return int(value)
        return None

    async def close(self) -> None:
        if self._page:
            await self._page.close()
            self._page = None
        if self._context:
            await self._context.close()
            self._context = None
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None


# ---- downloader.py ----

class PdfValidationError(ValueError):
    pass


class Downloader:
    def __init__(self, client, min_pdf_size: int = 1024):
        self._client = client
        self._min_pdf_size = min_pdf_size

    @staticmethod
    def _looks_like_pdf_headers(url: str, headers: dict[str, str]) -> bool:
        lower_headers = {k.lower(): v.lower() for k, v in headers.items()}
        content_type = lower_headers.get("content-type", "")
        content_disp = lower_headers.get("content-disposition", "")
        url_lower = url.lower()
        return (
            ".pdf" in url_lower
            or "application/pdf" in content_type
            or (".pdf" in content_disp and "filename" in content_disp)
        )

    def _validate_pdf_file(
        self,
        path: Path,
        size: int,
        url: str,
        headers: dict[str, str],
        require_network_signal: bool,
    ) -> None:
        if size < self._min_pdf_size:
            raise PdfValidationError(
                f"File too small ({size}B), likely not a valid PDF"
            )

        with open(path, "rb") as f:
            header = f.read(8)
        if not header.startswith(b"%PDF-"):
            raise PdfValidationError("Invalid PDF magic bytes")

        if require_network_signal and not self._looks_like_pdf_headers(url, headers):
            raise PdfValidationError("Missing PDF network/header signal")

    async def download(
        self,
        url: str,
        dest: Path,
        referer: str | None = None,
        require_network_signal: bool = False,
    ) -> tuple[Path, str, int]:
        dest = ensure_unique_path(dest)
        result = await self._client.download_file(url, dest, referer=referer)
        try:
            self._validate_pdf_file(
                path=dest,
                size=result.size,
                url=url,
                headers=result.headers,
                require_network_signal=require_network_signal,
            )
        except PdfValidationError:
            dest.unlink(missing_ok=True)
            raise
        hash_val = file_sha256(dest)
        logger.info("downloaded", path=str(dest), size=result.size, hash=hash_val[:12])
        return dest, hash_val, result.size

# ---- query_intent.py ----

@dataclass
class QueryIntent:
    subject: str | None = None
    grade: str | None = None
    exam_type: str | None = None


class QueryIntentParser:
    def __init__(self, config: IntentKeywordConfig):
        self._config = config

    def parse(self, query: str | None) -> QueryIntent:
        if not query:
            return QueryIntent()

        text = normalize_text(query)
        return QueryIntent(
            subject=self._detect(self._config.subjects, text),
            grade=self._detect(self._config.grades, text),
            exam_type=self._detect(self._config.exam_types, text),
        )

    def _detect(self, mapping: dict[str, list[str]], text: str) -> str | None:
        matched: tuple[str, int] | None = None
        for canonical, aliases in mapping.items():
            for alias in aliases:
                if contains_keyword(text, alias):
                    length = len(normalize_text(alias))
                    if matched is None or length > matched[1]:
                        matched = (canonical, length)
        return matched[0] if matched else None


# ---- crawl_service.py ----

@dataclass
class CrawlSummary:
    downloaded_count: int = 0
    documents: list[ExamDocument] = field(default_factory=list)

class CrawlService:
    HEADER_COMPARE_BYTES = 64 * 1024

    def __init__(self, settings: Settings):
        self._settings = settings
        self._last_crawler = None

    def _to_abs_path(self, local_path: str) -> Path:
        p = Path(local_path)
        if p.is_absolute():
            return p
        return (Path.cwd() / p).resolve()

    @staticmethod
    def _header_hash(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    def _local_header_hash(
        self, path: Path, max_bytes: int = HEADER_COMPARE_BYTES
    ) -> str | None:
        if not path.exists() or not path.is_file():
            return None
        with open(path, "rb") as f:
            chunk = f.read(max_bytes)
        if not chunk:
            return None
        return self._header_hash(chunk)

    async def _is_duplicate_by_size_and_header(
        self,
        db: aiosqlite.Connection,
        http,
        pdf_url: str,
        content_length: int | None,
    ) -> bool:
        if not content_length or content_length <= 1024:
            return False

        cur = await db.execute(
            "SELECT local_path FROM exam_documents WHERE file_size_bytes = ?",
            (content_length,),
        )
        rows = await cur.fetchall()
        if not rows:
            return False

        remote_header = await http.fetch_file_header(pdf_url, self.HEADER_COMPARE_BYTES)
        if not remote_header:
            return False
        remote_header_hash = self._header_hash(remote_header)

        for row in rows:
            local_path = self._to_abs_path(row["local_path"])
            local_header_hash = self._local_header_hash(
                local_path, self.HEADER_COMPARE_BYTES
            )
            if local_header_hash and local_header_hash == remote_header_hash:
                logger.info(
                    "skip_duplicate_size_and_header",
                    size=content_length,
                    local_path=str(local_path),
                    url=pdf_url,
                )
                return True
        return False


    @staticmethod
    def _split_downloaded_pdf(path: Path) -> Path | None:
        output_path = split_pdf_to_pdf(str(path))
        if not output_path:
            return None
        return Path(output_path).resolve()

    async def _hash_exists(self, db: aiosqlite.Connection, file_hash: str) -> bool:
        cur = await db.execute(
            "SELECT 1 FROM exam_documents WHERE file_hash = ?", (file_hash,)
        )
        return await cur.fetchone() is not None

    @staticmethod
    def _looks_like_pdf_candidate(url: str) -> bool:
        parsed = urlparse(url)
        path = parsed.path.lower()
        if path.endswith(".pdf"):
            return True
        for key in ("file", "url", "src", "download"):
            for value in parse_qs(parsed.query).get(key, []):
                if ".pdf" in unquote(value).lower():
                    return True
        return False

    @staticmethod
    def _is_explorable_url(url: str) -> bool:
        if _is_junk_url(url):
            return False

        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            return False
        path = parsed.path.lower()
        if path in {"", "/"}:
            return False
        if CrawlService._looks_like_pdf_candidate(url):
            return False
        if any(
            path.endswith(ext)
            for ext in (
                ".jpg",
                ".jpeg",
                ".png",
                ".gif",
                ".svg",
                ".css",
                ".js",
                ".ico",
                ".woff",
                ".woff2",
                ".zip",
                ".rar",
                ".doc",
                ".docx",
                ".xls",
                ".xlsx",
                ".ppt",
                ".pptx",
            )
        ):
            return False
        blocked = (
            "/wp-admin",
            "/wp-login",
            "/login",
            "/register",
            "/gioi-thieu",
            "/lien-he",
            "/privacy",
            "/policy",
        )
        if any(token in path for token in blocked):
            return False
        return True

    @staticmethod
    def _extract_grade_from_url(url: str) -> str | None:
        combined = unquote(url).lower()
        if re.search(r"(lop|khoi)[-_ ]*10|\b10\b", combined):
            return "10"
        if re.search(r"(lop|khoi)[-_ ]*11|\b11\b", combined):
            return "11"
        if re.search(r"(lop|khoi)[-_ ]*12|\b12\b", combined):
            return "12"
        if "thpt" in combined or "tot-nghiep" in combined or "tot nghiep" in combined:
            return "thpt"
        return None

    @staticmethod
    def _extract_exam_type_from_url(url: str) -> str | None:
        combined = normalize_text(unquote(url))
        if any(k in combined for k in ("giua hk1", "giua ky 1", "giua ki 1", "giua hoc ky 1", "giua hoc ki 1")):
            return "giua_hk1"
        if any(k in combined for k in ("hk1", "hoc ky 1", "hoc ki 1", "ky 1", "ki 1", "cuoi ky 1", "cuoi ki 1")):
            return "hk1"
        if any(k in combined for k in ("giua hk2", "giua ky 2", "giua ki 2", "giua hoc ky 2", "giua hoc ki 2")):
            return "giua_hk2"
        if any(k in combined for k in ("hk2", "hoc ky 2", "hoc ki 2", "ky 2", "ki 2", "cuoi ky 2", "cuoi ki 2")):
            return "hk2"
        if any(
            k in combined
            for k in (
                "khao sat",
                "khao-sat",
                "khao sat chat luong",
                "khao-sat-chat-luong",
                "kscl",
            )
        ):
            return "khao_sat"
        if any(
            k in combined
            for k in ("hsg", "hoc sinh gioi", "hoc-sinh-gioi", "de thi hsg", "de-thi-hsg")
        ):
            return "hsg"
        if any(
            k in combined
            for k in (
                "thptqg",
                "thpt-qg",
                "tnthpt",
                "tot-nghiep-thpt",
                "tot nghiep thpt",
                "thi-thpt-quoc-gia",
                "thi thpt quoc gia",
            )
        ):
            return "thptqg"
        if "thi-thu" in combined or "thi thu" in combined:
            return "thi_thu"
        if "de-cuong" in combined or "de cuong" in combined:
            return "de_cuong"
        return None


    def _matches_requested_url_pattern(
        self,
        url: str,
        allowed_subjects: set[str] | None,
        grade_filter: str | None,
        exam_type_filter: str | None,
    ) -> bool:
        subject = self._extract_subject_from_url(url)
        if allowed_subjects and subject and subject not in allowed_subjects:
            return False

        if grade_filter and self._extract_grade_from_url(url) != grade_filter:
            return False

        if exam_type_filter:
            return self._extract_exam_type_from_url(url) == exam_type_filter
        return True


    @staticmethod
    def _extract_subject_from_url(url: str) -> str | None:
        combined = canonicalize_subject(extract_subject("", unquote(url).lower()))
        return combined if combined != "unknown" else None


    @staticmethod
    def _is_pagination_url(url: str) -> bool:
        path = urlparse(url).path.lower()
        return bool(re.search(r"/page/\d+/?$", path))


    @staticmethod
    def _page_number(url: str) -> int:
        path = urlparse(url).path.lower()
        match = re.search(r"/page/(\d+)/?$", path)
        return int(match.group(1)) if match else 1


    @staticmethod
    def _pagination_base(url: str) -> str:
        parsed = urlparse(url)
        path = re.sub(r"/page/\d+/?$", "", parsed.path.rstrip("/"))
        return parsed._replace(path=path, query="", fragment="").geturl().rstrip("/")


    def _is_next_pagination_url(self, current_url: str, child_url: str) -> bool:
        if not self._is_pagination_url(child_url):
            return False
        if self._pagination_base(current_url) != self._pagination_base(child_url):
            return False
        return self._page_number(child_url) == self._page_number(current_url) + 1


    @staticmethod
    def _is_detail_url(url: str) -> bool:
        path = urlparse(url).path.lower()
        return path.endswith(".html") and re.search(r"/20\d{2}/\d{2}/", path) is not None


    def _child_group(self, current_url: str, child_url: str) -> int | None:
        if self._is_detail_url(child_url):
            return 0
        if self._is_next_pagination_url(current_url, child_url):
            return 1
        if self._is_pagination_url(child_url):
            return None
        return 2


    def _link_priority(
        self,
        url: str,
        allowed_subjects: set[str] | None,
        grade_filter: str | None,
        exam_type_filter: str | None,
        seed_tokens: set[str] | None = None,
    ) -> float:
        score = 0.0
        path = urlparse(url).path.lower()
        if self._is_detail_url(url):
            score += 20.0
        if "/chuyen-muc/" in path or "/tag/" in path or "/category/" in path:
            score += 3.0
        if self._is_pagination_url(url):
            score -= 10.0
        if self._looks_like_pdf_candidate(url):
            score -= 2.0

        subject = self._extract_subject_from_url(url)
        grade = self._extract_grade_from_url(url)
        exam_type = self._extract_exam_type_from_url(url)

        if allowed_subjects:
            if subject and subject in allowed_subjects:
                score += 8.0
            elif subject and subject not in allowed_subjects:
                score -= 4.0
        if grade_filter:
            if grade == grade_filter:
                score += 6.0
            elif grade and grade != grade_filter:
                score -= 3.0
        if exam_type_filter:
            if exam_type == exam_type_filter:
                score += 5.0
            elif exam_type and exam_type != exam_type_filter:
                score -= 2.5
        if seed_tokens:
            tokens = set(re.findall(r"[a-z0-9]{3,}", unquote(path)))
            overlap = len(tokens & seed_tokens)
            score += overlap * 1.5
        return score

    @staticmethod
    def _merge_pdf_urls(info_urls: list[str], captured: list[CapturedPdfUrl]) -> list[str]:
        merged: list[str] = []
        seen: set[str] = set()
        for url in info_urls + [item.url for item in captured]:
            if not url or url in seen:
                continue
            seen.add(url)
            merged.append(url)
        return merged

    @staticmethod
    def _build_signal_map(captured: list[CapturedPdfUrl]) -> dict[str, bool]:
        out: dict[str, bool] = {}
        for item in captured:
            out[item.url] = out.get(item.url, False) or item.has_network_pdf_signal()
        return out

    async def run(
        self,
        start_url: str,
        limit: int = 0,
        allowed_subjects: set[str] | None = None,
        grade_filter: str | None = None,
        exam_type_filter: str | None = None,
    ) -> int:
        summary = await self.run_with_summary(
            start_url=start_url,
            limit=limit,
            allowed_subjects=allowed_subjects,
            grade_filter=grade_filter,
            exam_type_filter=exam_type_filter,
        )
        return summary.downloaded_count


    async def run_with_summary(
        self,
        start_url: str,
        limit: int = 0,
        allowed_subjects: set[str] | None = None,
        grade_filter: str | None = None,
        exam_type_filter: str | None = None,
    ) -> CrawlSummary:
        parser = ToanMathParser()
        min_year = self._settings.priority.min_year
        logger.info("start_crawl", domain=parser.domain)
        summary = CrawlSummary()

        db = await get_db(self._settings.db_path)
        cache = DedupCache(db, self._settings.dedup.ttl_days)
        crawler = PlaywrightCrawlerClient(self._settings)
        self._last_crawler = crawler
        downloader = Downloader(crawler)
        detector = DownloadTargetDetector(self._settings.detectors)
        download_cache_marks: list[tuple[str, bool]] = []

        temp_run_dir = (
            self._settings.data_path
            / ".tmp_runs"
            / f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}"
        )
        tx = CrawlTransaction(db=db, temp_dir=temp_run_dir)

        downloaded = 0
        visited_in_run: set[str] = set()
        cache_status_in_run: dict[str, bool] = {}
        pages_processed = 0
        seed_tokens = set(re.findall(r"[a-z0-9]{3,}", unquote(urlparse(start_url).path.lower())))
        seed_tokens -= {"chuyen", "muc", "page", "html", "php", "de", "thi", "lop", "mon"}

        try:
            await tx.begin()

            async def is_cached(url: str) -> bool:
                if url not in cache_status_in_run:
                    cache_status_in_run[url] = await cache.is_crawled(url)
                return cache_status_in_run[url]


            async def crawl_link(link: str, depth: int, parent_url: str | None = None) -> None:
                nonlocal downloaded, pages_processed

                if limit > 0 and downloaded >= limit:
                    return
                if pages_processed >= self._settings.crawl.max_pages:
                    logger.info(
                        "max_pages_reached",
                        max_pages=self._settings.crawl.max_pages,
                        downloaded=downloaded,
                    )
                    return

                link = normalize_url(urldefrag(link)[0])
                if depth > self._settings.crawl.max_depth:
                    return
                if link in visited_in_run:
                    return
                if not parser.matches(link):
                    return
                if depth > 0 and not self._is_explorable_url(link):
                    return
                if depth > 0 and not self._matches_requested_url_pattern(
                    link,
                    allowed_subjects=allowed_subjects,
                    grade_filter=grade_filter,
                    exam_type_filter=exam_type_filter,
                ):
                    return

                visited_in_run.add(link)

                if await is_cached(link):
                    logger.debug("skip_cached", url=link, depth=depth)
                    return

                pages_processed += 1

                try:
                    page_html, captured_urls = await crawler.detect_pdf_urls(
                        link,
                        detector=detector,
                    )
                except PlaywrightError as e:
                    logger.warning("skip_page_error", url=link, error=str(e))
                    await crawler.close()
                    return
                signal_map = self._build_signal_map(captured_urls)
                info = parser.parse_detail_page(page_html, link)
                info.pdf_urls = self._merge_pdf_urls(info.pdf_urls, captured_urls)

                detected_subject = (
                    canonicalize_subject(info.subject) if info.subject else "unknown"
                )
                if detected_subject == "unknown":
                    detected_subject = canonicalize_subject(
                        extract_subject(info.title or "", link)
                    )
                info.subject = detected_subject

                child_links = parser.parse_listing_page(page_html, link)
                ranked_children: list[tuple[int, float, str]] = []
                for child in child_links:
                    child = normalize_url(urldefrag(child)[0])
                    if child in visited_in_run:
                        continue
                    if not parser.matches(child) or not self._is_explorable_url(child):
                        continue
                    if not self._matches_requested_url_pattern(
                        child,
                        allowed_subjects=allowed_subjects,
                        grade_filter=grade_filter,
                        exam_type_filter=exam_type_filter,
                    ):
                        continue
                    group = self._child_group(link, child)
                    if group is None:
                        continue
                    if await is_cached(child):
                        visited_in_run.add(child)
                        continue
                    ranked_children.append(
                        (
                            group,
                            self._link_priority(
                                child,
                                allowed_subjects=allowed_subjects,
                                grade_filter=grade_filter,
                                exam_type_filter=exam_type_filter,
                                seed_tokens=seed_tokens,
                            ),
                            child,
                        )
                    )
                ranked_children.sort(key=lambda item: (item[0], -item[1]))

                attempted_download = False
                downloaded_this_link = False
                had_duplicate = False
                should_try_download = True

                if min_year and info.year and info.year < min_year:
                    logger.debug("skip_old_year", year=info.year, min_year=min_year)
                    should_try_download = False

                if allowed_subjects and info.subject not in allowed_subjects:
                    logger.debug(
                        "skip_subject_not_selected",
                        subject=info.subject,
                        allowed_subjects=sorted(allowed_subjects),
                        url=link,
                    )
                    should_try_download = False

                if grade_filter and (info.grade or "") != grade_filter:
                    logger.debug(
                        "skip_grade_not_selected",
                        grade=info.grade,
                        grade_filter=grade_filter,
                        url=link,
                    )
                    should_try_download = False

                if exam_type_filter and (info.exam_type or "") != exam_type_filter:
                    logger.debug(
                        "skip_exam_type_not_selected",
                        exam_type=info.exam_type,
                        exam_type_filter=exam_type_filter,
                        url=link,
                    )
                    should_try_download = False

                if should_try_download:
                    for pdf_url in info.pdf_urls:
                        if _is_junk_url(pdf_url):
                            continue
                        if not self._looks_like_pdf_candidate(pdf_url):
                            logger.debug("skip_non_pdf_candidate", url=pdf_url, detail=link)
                            continue

                        attempted_download = True

                        dest_dir = build_pdf_path(
                            self._settings.storage_path,
                            info.subject,
                            info.grade,
                        )
                        filename = build_pdf_filename(
                            info.grade,
                            info.subject,
                            info.exam_type,
                            TOANMATH_DOMAIN,
                            school=info.province or "",
                            year=info.year,
                        )

                        content_length = await crawler.head_file_size(pdf_url)
                        if await self._is_duplicate_by_size_and_header(
                            db=db,
                            http=crawler,
                            pdf_url=pdf_url,
                            content_length=content_length,
                        ):
                            had_duplicate = True
                            continue

                        final_dest = ensure_unique_path(dest_dir / filename)
                        temp_dest = tx.build_temp_path(final_dest.name)

                        require_network_signal = signal_map.get(pdf_url, False)
                        try:
                            tmp_path, file_hash, size = await downloader.download(
                                pdf_url,
                                temp_dest,
                                referer=link,
                                require_network_signal=require_network_signal,
                            )
                        except PdfValidationError as e:
                            logger.warning(
                                "skip_invalid_pdf_candidate",
                                url=pdf_url,
                                detail=link,
                                error=str(e),
                            )
                            continue

                        if await self._hash_exists(db, file_hash):
                            tmp_path.unlink(missing_ok=True)
                            logger.info(
                                "skip_duplicate_hash",
                                hash=file_hash[:12],
                                url=pdf_url,
                            )
                            had_duplicate = True
                            continue

                        final_dest.parent.mkdir(parents=True, exist_ok=True)
                        tmp_path.replace(final_dest)
                        tx.register_final_file(final_dest)
                        try:
                            split_path = self._split_downloaded_pdf(final_dest)
                        except Exception as e:
                            logger.warning(
                                "split_pdf_failed",
                                path=str(final_dest),
                                error=str(e),
                            )
                            split_path = None
                        if split_path:
                            tx.register_final_file(split_path)
                        else:
                            final_dest.unlink(missing_ok=True)
                            attempted_download = False
                            logger.info(
                                "skip_without_final_output",
                                path=str(final_dest),
                            )
                            continue

                        doc = ExamDocument(
                            source_url=link,
                            source_domain=TOANMATH_DOMAIN,
                            pdf_url=pdf_url,
                            local_path=str(final_dest.resolve()),
                            file_hash=file_hash,
                            file_size_bytes=size,
                            title=info.title,
                            grade=info.grade,
                            subject=info.subject,
                            exam_type=info.exam_type,
                            year=info.year,
                        )

                        await db.execute(
                            """INSERT INTO exam_documents
                               (source_url, source_domain, pdf_url, local_path, file_hash, file_size_bytes,
                                title, grade, subject, exam_type, year)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            (
                                doc.source_url,
                                doc.source_domain,
                                doc.pdf_url,
                                doc.local_path,
                                doc.file_hash,
                                doc.file_size_bytes,
                                doc.title,
                                doc.grade,
                                doc.subject,
                                doc.exam_type,
                                doc.year,
                            ),
                        )

                        downloaded += 1
                        summary.downloaded_count += 1
                        summary.documents.append(doc)
                        downloaded_this_link = True
                        break

                if not downloaded_this_link:
                    for _, _score, child in ranked_children:
                        await crawl_link(child, depth + 1, parent_url=link)
                        if limit > 0 and downloaded >= limit:
                            break

                if attempted_download:
                    download_cache_marks.append((link, downloaded_this_link or had_duplicate))
                await crawler.go_back_to(parent_url)

            await crawl_link(start_url, 0, parent_url=None)
            
            await tx.commit()
            for url, has_pdf in download_cache_marks:
                await cache.mark_crawled(url, has_pdf=has_pdf, commit=False)
            await db.commit()

            logger.info("deep_crawl_complete", downloaded=downloaded)
            return summary

        except Exception as e:
            logger.error("crawl_failed_abort", error=str(e), downloaded=downloaded)
            await tx.rollback()
            raise
        finally:
            await crawler.close()
            await db.close()

    async def clear_cache(self) -> int:
        db = await get_db(self._settings.db_path)
        try:
            cache = DedupCache(db, self._settings.dedup.ttl_days)
            return await cache.clear(TOANMATH_DOMAIN)
        finally:
            await db.close()
