from __future__ import annotations

import re
from bs4 import BeautifulSoup

from exam_scraper.spiders.base_spider import BaseSpider
from exam_scraper.db.models import ExamInfo
from exam_scraper.core.pdf_extractor import PdfExtractor
from exam_scraper.utils.url_utils import extract_year


class Thi247Spider(BaseSpider):
    domain = "thi247.com"
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
        
        # subject detection
        subjects = ["toan", "vat-ly", "hoa-hoc", "sinh-hoc", "tieng-anh", "ngu-van", "lich-su", "dia-ly", "gdcd"]
        for sub in subjects:
            if sub in url_lower:
                info.subject = sub.replace("-", "")
                break
                
        if not info.subject and "ly" in url_lower:
            info.subject = "vatly"
            
        # grade detection
        if "10" in url_lower:
            info.grade = "10"
        elif "11" in url_lower:
            info.grade = "11"
        elif "12" in url_lower:
            info.grade = "12"
        elif "thpt" in url_lower:
            info.grade = "thpt"
            
        # exam type
        search_str = url_lower + " " + title.lower()
        if "giua-hk1" in search_str or "giua-ki-1" in search_str or "giua-hoc-ki-1" in search_str or "giữa học kì 1" in search_str:
            info.exam_type = "giua_hk1"
        elif "hk1" in search_str or "ki-1" in search_str or "hoc-ki-1" in search_str or "học kì 1" in search_str:
            info.exam_type = "hk1"
        elif "giua-hk2" in search_str or "giua-ki-2" in search_str or "giua-hoc-ki-2" in search_str or "giữa học kì 2" in search_str:
            info.exam_type = "giua_hk2"
        elif "hk2" in search_str or "ki-2" in search_str or "hoc-ki-2" in search_str or "học kì 2" in search_str:
            info.exam_type = "hk2"
        elif "thi-thu" in search_str or "thi thử" in search_str:
            info.exam_type = "thi_thu"

        return info
