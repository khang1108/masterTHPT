from __future__ import annotations

import re
from bs4 import BeautifulSoup

from exam_scraper.spiders.base_spider import BaseSpider
from exam_scraper.db.models import ExamInfo
from exam_scraper.core.pdf_extractor import PdfExtractor
from exam_scraper.utils.url_utils import extract_year, extract_school, extract_subject

class GenericSpider(BaseSpider):
    domain = "*"
    tier = "T3"

    def __init__(self):
        self._extractor = PdfExtractor()

    def parse_listing_page(self, html: str, url: str) -> list[str]:
        return self._extractor.extract_listing_links(html, url)

    def parse_detail_page(self, html: str, url: str) -> ExamInfo:
        soup = BeautifulSoup(html, "html.parser")
        
        title_tag = soup.find("h1") or soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else ""
        
        info = ExamInfo(
            title=title,
            pdf_urls=self._extractor.extract_from_html(html, url),
            year=extract_year(title) or extract_year(url),
            subject=extract_subject(title, url),
            province=extract_school(title),
        )

        url_lower = url.lower()
        if "10" in url_lower:
            info.grade = "10"
        elif "11" in url_lower:
            info.grade = "11"
        elif "12" in url_lower:
            info.grade = "12"
        elif "thpt" in url_lower:
            info.grade = "thpt"
            
        return info
            
        return info

    def matches(self, url: str) -> bool:
        return True
