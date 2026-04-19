from exam_scraper.config import Settings
from exam_scraper.core import DownloadTargetDetector


def test_download_detector_ranks_pdf_candidate_first():
    detector = DownloadTargetDetector(Settings().detectors)
    ranked = detector.rank(
        [
            {
                "text": "Liên hệ quảng cáo",
                "href": "/contact",
                "aria_label": "",
                "title": "",
                "class_name": "footer-link",
                "element_id": "",
                "nearby_text": "",
            },
            {
                "text": "Tải PDF đề thi",
                "href": "/files/de-thi-toan-12.pdf",
                "aria_label": "download pdf",
                "title": "",
                "class_name": "btn-download",
                "element_id": "download",
                "nearby_text": "",
            },
            {
                "text": "Đăng nhập",
                "href": "/login",
                "aria_label": "",
                "title": "",
                "class_name": "",
                "element_id": "",
                "nearby_text": "",
            },
        ]
    )

    assert ranked[0].href.endswith(".pdf")
    assert ranked[0].score > ranked[1].score
    assert ranked[-1].score < 0
