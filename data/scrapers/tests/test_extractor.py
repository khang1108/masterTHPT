import pytest
from exam_scraper.core.pdf_extractor import PdfExtractor

def test_pdf_extractor():
    ext = PdfExtractor()
    html = """
    <html>
        <a href="https://example.com/doc.pdf">Direct</a>
        <a href="https://drive.google.com/file/d/123abcXYZ/view">Drive Viewer</a>
        <a href="/download.html">Tải đề</a>
        <a href="/other">Not relevant</a>
    </html>
    """
    links = ext.extract_from_html(html, "https://example.com")
    
    assert "https://example.com/doc.pdf" in links
    assert "https://drive.google.com/uc?export=download&id=123abcXYZ" in links
    assert "https://example.com/download.html" in links
    assert "https://example.com/other" not in links
