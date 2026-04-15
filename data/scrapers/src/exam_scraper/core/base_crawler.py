from __future__ import annotations

from abc import ABC, abstractmethod
from exam_scraper.db.models import ExamInfo


class BaseCrawler(ABC):
    @abstractmethod
    async def discover_urls(self, **kwargs) -> list[str]:
        ...

    @abstractmethod
    async def extract_pdf_links(self, url: str) -> list[str]:
        ...

    @abstractmethod
    async def run(self, **kwargs) -> list[dict]:
        ...
