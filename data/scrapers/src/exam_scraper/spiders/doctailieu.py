from __future__ import annotations

import re
from bs4 import BeautifulSoup

from exam_scraper.spiders.base_spider import BaseSpider
from exam_scraper.db.models import ExamInfo
from exam_scraper.core.pdf_extractor import PdfExtractor
from exam_scraper.utils.url_utils import extract_year


class DocTaiLieuSpider(BaseSpider):
    domain = "doctailieu.com"
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
            pdf_urls=self._extractor.extract_from_html(html, url),
            year=extract_year(title) or extract_year(url),
        )

        url_lower = url.lower()
        
        subjects = ["toan", "ly", "hoa", "sinh", "anh", "van", "su", "dia", "gdcd", "tin", "cong-nghe"]
        for sub in subjects:
            if f"-{sub}-" in url_lower or f"mon-{sub}" in url_lower:
                info.subject = sub.replace("-", "")
                break
                
        if "lop-10" in url_lower or "vao-10" in url_lower or "-10-" in url_lower:
            info.grade = "10"
        elif "lop-11" in url_lower or "-11-" in url_lower:
            info.grade = "11"
        elif "lop-12" in url_lower or "-12-" in url_lower:
            info.grade = "12"
        elif "thpt" in url_lower:
            info.grade = "thpt"
            
        if "giua-hoc-ki-1" in url_lower or "giua-hk1" in url_lower:
            info.exam_type = "giua_hk1"
        elif "hoc-ki-1" in url_lower or "-hk1" in url_lower:
            info.exam_type = "hk1"
        elif "giua-hoc-ki-2" in url_lower or "giua-hk2" in url_lower:
            info.exam_type = "giua_hk2"
        elif "hoc-ki-2" in url_lower or "-hk2" in url_lower:
            info.exam_type = "hk2"
        elif "thi-thu" in url_lower:
            info.exam_type = "thi_thu"

        return info
