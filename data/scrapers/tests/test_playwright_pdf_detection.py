from exam_scraper.core.playwright_crawler import (
    _extract_embedded_pdf_url,
    _is_pdf_like,
    _is_static_asset_url,
)


def test_is_pdf_like_for_direct_pdf_and_query_embedded_pdf():
    assert _is_pdf_like("https://example.com/files/de-thi.pdf")
    assert _is_pdf_like(
        "https://example.com/viewer.html?file=https%3A%2F%2Fcdn.example.com%2Fa.pdf"
    )


def test_is_pdf_like_rejects_pdf_word_in_non_pdf_asset():
    assert not _is_pdf_like(
        "https://example.com/images/toolbarButton-download.svg"
    )
    assert _is_static_asset_url(
        "https://example.com/images/toolbarButton-download.svg"
    )


def test_extract_embedded_pdf_url_from_viewer_query():
    out = _extract_embedded_pdf_url(
        "https://thi247.com/wp-content/plugins/wonderplugin-pdf-embed/pdfjslight/web/viewer.html"
        "?v=2&file=https%3A%2F%2Fthi247.com%2Fthi247-pdf%2Fde-1.pdf"
    )
    assert out == "https://thi247.com/thi247-pdf/de-1.pdf"
