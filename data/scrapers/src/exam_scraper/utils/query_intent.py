from __future__ import annotations

from dataclasses import dataclass

from exam_scraper.config import IntentKeywordConfig
from exam_scraper.core.detectors import contains_keyword, normalize_text


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
