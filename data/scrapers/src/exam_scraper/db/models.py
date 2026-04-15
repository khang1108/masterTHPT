from __future__ import annotations

from dataclasses import dataclass, field


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
