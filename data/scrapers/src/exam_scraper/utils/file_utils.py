from __future__ import annotations

import re
import hashlib
from pathlib import Path


def sanitize_filename(name: str) -> str:
    name = re.sub(r'[<>:"/\\|?*]', "_", name)
    name = re.sub(r"\s+", "_", name)
    name = re.sub(r"_+", "_", name)
    return name.strip("_").lower()


def build_pdf_path(
    storage_dir: Path,
    domain: str,
    grade: str,
    subject: str,
    exam_type: str,
) -> Path:
    grade_dir = f"lop-{grade}" if grade != "thpt" else "thpt"
    path = storage_dir / domain / grade_dir / subject / exam_type
    path.mkdir(parents=True, exist_ok=True)
    return path


def build_pdf_filename(
    grade: str,
    subject: str,
    exam_type: str,
    source: str,
    school: str = "",
    suffix: str = "",
) -> str:
    source_clean = source.replace(".", "").replace("www", "")
    parts = [grade, subject]
    if school:
        parts.append(school)
    else:
        parts.append(exam_type)
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
