import pytest
from exam_scraper.utils.url_utils import extract_subject

def test_extract_subject():
    assert extract_subject("Đề thi Toán lớp 12", "https://url.com/abc") == "toan"
    assert extract_subject("Đề thi Ngữ văn THPT", "https://url.com") == "van"
    assert extract_subject("Môn Vật lí 11", "https://url.com") == "ly"
    assert extract_subject("Đề thi môn Lịch sử", "https://url.com/dia") == "su"
    assert extract_subject("Kinh tế và pháp luật lớp 10", "https://a.com") == "gdktpl"
    assert extract_subject("Đề thi thpt nhanh chóng", "https://a.com") == "unknown" # Ensures 'anh' inside 'nhanh' doesn't match
