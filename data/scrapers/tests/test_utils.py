import pytest
from exam_scraper.utils.url_utils import extract_year, url_hash, canonicalize_subject
from exam_scraper.utils.file_utils import sanitize_filename

def test_extract_year():
    assert extract_year("Đề thi Toán lớp 12 năm 2024") == 2024
    assert extract_year("HK1 2023-2024") == 2024
    assert extract_year("No year here") is None

def test_sanitize_filename():
    assert sanitize_filename("de/thi:toan  abc") == "de_thi_toan_abc"

def test_url_hash():
    h1 = url_hash("https://example.com/A B?param=1/")
    h2 = url_hash("https://example.com/A%20B")
    assert h1 == h2

def test_canonicalize_subject():
    assert canonicalize_subject("vat-ly") == "ly"
    assert canonicalize_subject("vatly") == "ly"
    assert canonicalize_subject("ngu_van") == "van"
    assert canonicalize_subject("tieng-anh") == "anh"
    assert canonicalize_subject("cong-nghe") == "cong_nghe"
