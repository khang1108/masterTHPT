import pytest
from exam_scraper.spiders.thi247 import Thi247Spider

def test_thi247_parse_detail():
    spider = Thi247Spider()
    html = """<h1>Đề thi học kì 1 Toán 12 năm 2023 2024</h1><a href="/file.pdf">PDF</a>"""
    info = spider.parse_detail_page(html, "https://thi247.com/de-thi-toan-12/")
    
    assert info.title == "Đề thi học kì 1 Toán 12 năm 2023 2024"
    assert "https://thi247.com/file.pdf" in info.pdf_urls
    assert info.year == 2024
    assert info.grade == "12"
    assert info.subject == "toan"
    assert info.exam_type == "hk1"
