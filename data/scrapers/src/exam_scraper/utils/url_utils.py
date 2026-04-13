from __future__ import annotations

import re
import hashlib
import unicodedata
from urllib.parse import urlparse, urlunparse, urljoin, unquote, quote

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


def is_same_domain(url: str, domain: str) -> bool:
    return extract_domain(url) == domain.lower()


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
