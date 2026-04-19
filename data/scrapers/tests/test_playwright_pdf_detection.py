from types import SimpleNamespace

import pytest

import exam_scraper.core as playwright_client_module
from exam_scraper.config import Settings
from exam_scraper.core import DownloadTargetDetector
from exam_scraper.core import (
    PlaywrightCrawlerClient,
    _extract_embedded_pdf_url,
    _is_pdf_like,
    _is_junk_url,
    _is_static_asset_url,
)
from exam_scraper.core import CrawlService
from exam_scraper.core import normalize_url


class _FakePage:
    def __init__(self):
        self.url = ""
        self.goto_calls: list[str] = []
        self.go_back_calls = 0
        self._closed = False
        self._listeners: dict[str, list] = {}
        self.history: list[str] = []
        self.main_frame = object()
        self.frames = [self.main_frame]
        self.bad_back_url: str | None = None
        self.raw_candidates: list[dict] = []
        self.handles: list[object] = []
        self.evaluate_calls: list[str] = []

    def is_closed(self) -> bool:
        return self._closed

    def on(self, event: str, callback) -> None:
        self._listeners.setdefault(event, []).append(callback)

    def remove_listener(self, event: str, callback) -> None:
        listeners = self._listeners.get(event, [])
        if callback in listeners:
            listeners.remove(callback)

    async def goto(self, url: str, wait_until: str | None = None, timeout: int | None = None):
        self.url = url
        self.goto_calls.append(url)
        self.history.append(url)

    async def go_back(
        self,
        wait_until: str | None = None,
        timeout: int | None = None,
    ):
        self.go_back_calls += 1
        if self.bad_back_url:
            self.url = self.bad_back_url
            return object()
        if len(self.history) < 2:
            return None
        self.history.pop()
        self.url = self.history[-1]
        return object()

    async def content(self) -> str:
        return "<html></html>"

    async def evaluate(self, script: str):
        self.evaluate_calls.append(script)
        return None

    async def eval_on_selector_all(self, selector: str, script: str):
        return self.raw_candidates

    async def query_selector_all(self, selector: str):
        return self.handles

    async def wait_for_timeout(self, ms: int) -> None:
        return None

    async def close(self) -> None:
        self._closed = True


class _FakeContext:
    def __init__(self, page: _FakePage):
        self.page = page
        self.new_page_calls = 0
        self.request = SimpleNamespace(fetch=None)

    async def new_page(self):
        self.new_page_calls += 1
        return self.page

    async def close(self) -> None:
        return None


class _FakeBrowser:
    def __init__(self, context: _FakeContext):
        self.context = context

    async def new_context(self, **kwargs):
        return self.context

    async def close(self) -> None:
        return None


class _FakeDriver:
    def __init__(self, browser: _FakeBrowser):
        self.browser = browser
        self.chromium = SimpleNamespace(launch=self._launch)

    async def _launch(self, headless: bool):
        return self.browser

    async def stop(self) -> None:
        return None


class _FakeStarter:
    def __init__(self, driver: _FakeDriver):
        self.driver = driver

    async def start(self):
        return self.driver


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


def test_junk_url_filter_blocks_ads_and_recaptcha_noise():
    assert _is_junk_url("about:blank")
    assert _is_junk_url("https://www.google.com/recaptcha/api2/aframe")
    assert _is_junk_url("https://ep2.adtrafficquality.google/sodar/sodar2/runner.html")
    assert _is_junk_url("https://googleads.g.doubleclick.net/pagead/ads?client=x")
    assert not _is_junk_url("https://toanmath.com/2026/01/de-thi-toan-12.html")


def test_extract_embedded_pdf_url_from_viewer_query():
    out = _extract_embedded_pdf_url(
        "https://toanmath.com/wp-content/plugins/wonderplugin-pdf-embed/pdfjslight/web/viewer.html"
        "?v=2&file=https%3A%2F%2Ftoanmath.com%2Ffiles%2Fde-1.pdf"
    )
    assert out == "https://toanmath.com/files/de-1.pdf"


def test_crawl_service_does_not_explore_pdf_candidate_urls():
    assert not CrawlService._is_explorable_url("https://toanmath.com/files/de-thi.pdf")
    assert not CrawlService._is_explorable_url(
        "https://toanmath.com/viewer.html?file=https%3A%2F%2Ftoanmath.com%2Ffiles%2Fde.pdf"
    )
    assert not CrawlService._is_explorable_url("https://www.google.com/recaptcha/api2/aframe")


@pytest.mark.asyncio
async def test_playwright_client_reuses_single_page(monkeypatch):
    page = _FakePage()
    context = _FakeContext(page)
    browser = _FakeBrowser(context)
    driver = _FakeDriver(browser)
    monkeypatch.setattr(
        playwright_client_module,
        "async_playwright",
        lambda: _FakeStarter(driver),
    )

    settings = Settings()
    client = PlaywrightCrawlerClient(settings)
    detector = DownloadTargetDetector(settings.detectors)

    await client.detect_pdf_urls("https://toanmath.com/a.html", detector)
    await client.detect_pdf_urls("https://toanmath.com/b.html", detector)
    await client.close()

    assert context.new_page_calls == 1
    assert page.goto_calls == [
        "https://toanmath.com/a.html",
        "https://toanmath.com/b.html",
    ]
    assert len(page.evaluate_calls) == 2
    assert all("scrollTo" in script for script in page.evaluate_calls)
    assert client.clicked_history == [
        normalize_url("https://toanmath.com/a.html"),
        normalize_url("https://toanmath.com/b.html"),
    ]


@pytest.mark.asyncio
async def test_playwright_client_falls_back_to_goto_when_go_back_misses_parent(monkeypatch):
    page = _FakePage()
    context = _FakeContext(page)
    browser = _FakeBrowser(context)
    driver = _FakeDriver(browser)
    monkeypatch.setattr(
        playwright_client_module,
        "async_playwright",
        lambda: _FakeStarter(driver),
    )

    settings = Settings()
    client = PlaywrightCrawlerClient(settings)

    await client.goto("https://toanmath.com/parent.html")
    await client.goto("https://toanmath.com/child.html")
    page.bad_back_url = "https://toanmath.com/wrong.html"

    await client.go_back_to("https://toanmath.com/parent.html")

    assert page.go_back_calls == 1
    assert page.goto_calls[-1] == "https://toanmath.com/parent.html"


@pytest.mark.asyncio
async def test_playwright_client_does_not_click_when_href_candidate_exists(monkeypatch):
    page = _FakePage()
    page.raw_candidates = [
        {
            "text": "Download PDF",
            "href": "/files/de-thi.pdf",
            "aria_label": "",
            "title": "",
            "class_name": "",
            "element_id": "",
            "nearby_text": "",
        }
    ]
    page.handles = [object()]
    context = _FakeContext(page)
    browser = _FakeBrowser(context)
    driver = _FakeDriver(browser)
    monkeypatch.setattr(
        playwright_client_module,
        "async_playwright",
        lambda: _FakeStarter(driver),
    )

    settings = Settings()
    client = PlaywrightCrawlerClient(settings)
    detector = DownloadTargetDetector(settings.detectors)

    html, captured = await client.detect_pdf_urls("https://toanmath.com/a.html", detector)

    assert html == "<html></html>"
    assert [item.url for item in captured] == ["https://toanmath.com/files/de-thi.pdf"]


@pytest.mark.asyncio
async def test_playwright_client_does_not_capture_navigation_href_as_pdf(monkeypatch):
    page = _FakePage()
    page.raw_candidates = [
        {
            "text": "Tài liệu ôn thi",
            "href": "/tai-lieu-on-thi-thpt-mon-toan",
            "aria_label": "",
            "title": "",
            "class_name": "",
            "element_id": "",
            "nearby_text": "",
        }
    ]
    page.handles = [object()]
    context = _FakeContext(page)
    browser = _FakeBrowser(context)
    driver = _FakeDriver(browser)
    monkeypatch.setattr(
        playwright_client_module,
        "async_playwright",
        lambda: _FakeStarter(driver),
    )

    settings = Settings()
    client = PlaywrightCrawlerClient(settings)
    detector = DownloadTargetDetector(settings.detectors)

    _html, captured = await client.detect_pdf_urls("https://toanmath.com/a.html", detector)

    assert captured == []
