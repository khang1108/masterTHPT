from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Any

from exam_scraper.config import DetectorConfig


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
