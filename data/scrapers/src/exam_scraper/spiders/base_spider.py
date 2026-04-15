from __future__ import annotations

from abc import ABC, abstractmethod
from exam_scraper.db.models import ExamInfo

class BaseSpider(ABC):
    domain: str
    tier: str

    @abstractmethod
    def parse_listing_page(self, html: str, url: str) -> list[str]:
        ...

    @abstractmethod
    def parse_detail_page(self, html: str, url: str) -> ExamInfo:
        ...

    def matches(self, url: str) -> bool:
        from exam_scraper.utils.url_utils import is_same_domain
        return is_same_domain(url, self.domain)
