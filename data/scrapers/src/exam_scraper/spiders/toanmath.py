from __future__ import annotations

from bs4 import BeautifulSoup

from exam_scraper.spiders.base_spider import BaseSpider
from exam_scraper.db.models import ExamInfo
from exam_scraper.core.pdf_extractor import PdfExtractor
from exam_scraper.utils.url_utils import extract_year, extract_school, extract_subject


class ToanMathSpider(BaseSpider):
    domain = "toanmath.com"
    tier = "T1"

    def __init__(self):
        self._extractor = PdfExtractor()

    def parse_listing_page(self, html: str, url: str) -> list[str]:
        return self._extractor.extract_listing_links(html, url)

    def parse_detail_page(self, html: str, url: str) -> ExamInfo:
        soup = BeautifulSoup(html, "html.parser")
        
        title_tag = soup.find("h1")
        title = title_tag.get_text(strip=True) if title_tag else ""
        
        info = ExamInfo(
            title=title,
            subject="toan",
            pdf_urls=self._extractor.extract_from_html(html, url),
            year=extract_year(title) or extract_year(url),
            province=extract_school(title),
        )

        url_lower = url.lower()
        if "toan-10" in url_lower or "lop-10" in url_lower:
            info.grade = "10"
        elif "toan-11" in url_lower or "lop-11" in url_lower:
            info.grade = "11"
        elif "toan-12" in url_lower or "lop-12" in url_lower:
            info.grade = "12"
        elif "thpt" in url_lower:
            info.grade = "thpt"
            
        if "giua-hk1" in url_lower or "giua-ky-1" in url_lower:
            info.exam_type = "giua_hk1"
        elif "hk1" in url_lower or "hoc-ky-1" in url_lower:
            info.exam_type = "hk1"
        elif "giua-hk2" in url_lower or "giua-ky-2" in url_lower:
            info.exam_type = "giua_hk2"
        elif "hk2" in url_lower or "hoc-ky-2" in url_lower:
            info.exam_type = "hk2"
        elif "de-cuong" in url_lower:
            info.exam_type = "de_cuong"
        elif "thi-thu" in url_lower:
            info.exam_type = "thi_thu"

        return info
