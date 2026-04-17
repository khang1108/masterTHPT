from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import parse_qs, unquote, urldefrag, urlparse

import structlog
from playwright.async_api import (
    APIResponse,
    Browser,
    BrowserContext,
    Error as PlaywrightError,
    Page,
    TimeoutError as PlaywrightTimeoutError,
    async_playwright,
)

from exam_scraper.config import Settings
from exam_scraper.core.detectors import DownloadTargetDetector, normalize_text
from exam_scraper.core.pdf_extractor import PdfExtractor
from exam_scraper.utils.url_utils import (
    extract_gdrive_id,
    gdrive_direct_url,
    is_pdf_url,
    resolve_url,
)

logger = structlog.get_logger()


@dataclass
class DownloadResult:
    size: int
    status_code: int
    headers: dict[str, str]


@dataclass
class CapturedPdfUrl:
    url: str
    content_type: str = ""
    content_disposition: str = ""
    source: str = ""

    def has_network_pdf_signal(self) -> bool:
        return _is_pdf_like(self.url, self.content_type, self.content_disposition)


_STATIC_ASSET_EXTENSIONS = {
    ".svg",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".ico",
    ".css",
    ".js",
    ".map",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
}


def _normalize_capture_url(url: str) -> str:
    if not url:
        return ""
    clean, _fragment = urldefrag(url.strip())
    return clean


def _is_static_asset_url(url: str) -> bool:
    path = urlparse(url).path.lower()
    return any(path.endswith(ext) for ext in _STATIC_ASSET_EXTENSIONS)


def _extract_embedded_pdf_url(url: str) -> str | None:
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    for key in ("file", "url", "src", "download"):
        for value in query.get(key, []):
            unquoted = unquote(value).strip()
            if _is_pdf_like(unquoted):
                return _normalize_capture_url(unquoted)
    return None


def _is_pdf_like(
    url: str, content_type: str | None = None, content_disposition: str | None = None
) -> bool:
    parsed = urlparse(url)
    path = parsed.path.lower()
    query = parse_qs(parsed.query)
    ct_norm = normalize_text(content_type or "")
    cd_norm = normalize_text(content_disposition or "")
    if path.endswith(".pdf"):
        return True
    for key in ("file", "url", "src", "download"):
        for value in query.get(key, []):
            value_norm = normalize_text(unquote(value))
            if ".pdf" in value_norm:
                return True
    if "application/pdf" in ct_norm:
        return True
    if "filename=" in cd_norm and ".pdf" in cd_norm:
        return True
    return False


class PlaywrightCrawlerClient:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._playwright = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None

    async def _ensure_context(self) -> BrowserContext:
        if self._context is not None:
            return self._context

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=self._settings.playwright.headless
        )
        self._context = await self._browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="vi-VN",
            accept_downloads=True,
        )
        logger.info("playwright_context_ready")
        return self._context

    async def get_page(self) -> Page:
        context = await self._ensure_context()
        return await context.new_page()

    async def fetch_rendered(self, url: str) -> str:
        page = await self.get_page()
        try:
            await page.goto(
                url,
                wait_until="networkidle",
                timeout=self._settings.playwright.timeout,
            )
            return await page.content()
        finally:
            await page.close()

    async def detect_pdf_urls(
        self,
        detail_url: str,
        detector: DownloadTargetDetector,
        extractor: PdfExtractor,
    ) -> tuple[str, list[CapturedPdfUrl]]:
        context = await self._ensure_context()
        page = await context.new_page()
        captured: list[CapturedPdfUrl] = []
        seen: set[str] = set()

        def _capture(
            url: str,
            content_type: str = "",
            content_disposition: str = "",
            source: str = "",
        ) -> None:
            normalized = _normalize_capture_url(url)
            if (
                not normalized
                or normalized in seen
                or _is_static_asset_url(normalized)
            ):
                return
            seen.add(normalized)
            captured.append(
                CapturedPdfUrl(
                    url=normalized,
                    content_type=content_type or "",
                    content_disposition=content_disposition or "",
                    source=source,
                )
            )
            embedded = _extract_embedded_pdf_url(normalized)
            if embedded and embedded not in seen and not _is_static_asset_url(embedded):
                seen.add(embedded)
                captured.append(
                    CapturedPdfUrl(
                        url=embedded,
                        content_type="application/pdf",
                        content_disposition="",
                        source=f"{source}_embedded",
                    )
                )

        def _on_response(response) -> None:
            headers = {k.lower(): v for k, v in response.headers.items()}
            url = str(response.url or "")
            ctype = headers.get("content-type", "")
            cdisp = headers.get("content-disposition", "")
            if _is_pdf_like(url, ctype, cdisp):
                _capture(url, ctype, cdisp, "response")

        def _on_request(request) -> None:
            url = str(request.url or "")
            if _is_pdf_like(url):
                _capture(url, source="request")

        page.on("response", _on_response)
        page.on("request", _on_request)

        try:
            await page.goto(
                detail_url,
                wait_until="networkidle",
                timeout=self._settings.playwright.timeout,
            )
            html = await page.content()

            # Static extraction from rendered DOM still helps when link is directly exposed.
            for url in extractor.extract_from_html(html, detail_url):
                _capture(url, source="dom")
            for frame in page.frames:
                if frame == page.main_frame:
                    continue
                if frame.url:
                    _capture(str(frame.url), source="frame_url")

            # Known PDFJS/WonderPlugin viewer: click download button inside iframe if available.
            for frame in page.frames:
                if frame == page.main_frame:
                    continue
                frame_url = str(frame.url or "").lower()
                if "viewer" not in frame_url and "pdfjs" not in frame_url:
                    continue
                try:
                    button = frame.locator("#download")
                    if await button.count() > 0:
                        await button.first.click(timeout=1500, force=True)
                        await page.wait_for_timeout(self._settings.detectors.network_wait_ms)
                except PlaywrightError:
                    continue

            raw_candidates = await page.eval_on_selector_all(
                "a,button,[role='button'],[onclick],[data-href]",
                """(elements) => elements.slice(0, 300).map((el) => ({
                    text: (el.innerText || el.textContent || "").trim().slice(0, 240),
                    href: (el.getAttribute("href") || el.getAttribute("data-href") || "").trim(),
                    aria_label: (el.getAttribute("aria-label") || "").trim(),
                    title: (el.getAttribute("title") || "").trim(),
                    class_name: String(el.className || "").trim(),
                    element_id: (el.id || "").trim(),
                    nearby_text: ((el.parentElement && el.parentElement.innerText) || "").trim().slice(0, 240)
                }))""",
            )
            ranked = detector.rank(raw_candidates)
            handles = await page.query_selector_all(
                "a,button,[role='button'],[onclick],[data-href]"
            )

            # Direct href candidates should be considered before click.
            for candidate in ranked[: self._settings.detectors.max_click_attempts]:
                href = candidate.href.strip()
                if not href:
                    continue
                absolute = resolve_url(detail_url, href)
                gid = extract_gdrive_id(absolute)
                if gid:
                    absolute = gdrive_direct_url(gid)
                if is_pdf_url(absolute) or candidate.score > 0:
                    _capture(absolute, source="href")

            for candidate in ranked[: self._settings.detectors.max_click_attempts]:
                if candidate.score <= 0:
                    continue
                if candidate.index >= len(handles):
                    continue
                handle = handles[candidate.index]
                before_count = len(captured)

                try:
                    async with page.expect_download(
                        timeout=self._settings.detectors.network_wait_ms
                    ) as download_info:
                        await handle.click(timeout=2000, force=True)
                    download = await download_info.value
                    download_url = str(download.url or "")
                    if download_url:
                        _capture(download_url, source="download_event")
                except PlaywrightTimeoutError:
                    try:
                        await handle.click(timeout=2000, force=True)
                        await page.wait_for_timeout(self._settings.detectors.network_wait_ms)
                    except PlaywrightError:
                        continue
                except PlaywrightError:
                    continue

                current_url = str(page.url or "")
                if _is_pdf_like(current_url):
                    _capture(current_url, source="post_click_url")
                if len(captured) > before_count:
                    break

            source_priority = {
                "download_event": 100,
                "response": 90,
                "request_embedded": 85,
                "response_embedded": 85,
                "frame_url_embedded": 83,
                "href": 70,
                "dom": 60,
                "request": 50,
                "post_click_url": 40,
                "frame_url": 30,
            }

            def _priority(item: CapturedPdfUrl) -> int:
                base = source_priority.get(item.source, 10)
                if urlparse(item.url).path.lower().endswith(".pdf"):
                    base += 20
                return base

            captured.sort(key=_priority, reverse=True)
            return html, captured
        finally:
            await page.close()

    async def head_file_size(self, url: str) -> int | None:
        context = await self._ensure_context()
        response = await context.request.fetch(
            url,
            method="HEAD",
            timeout=self._settings.playwright.timeout,
        )
        return self._extract_content_length(response)

    async def fetch_file_header(self, url: str, max_bytes: int = 65536) -> bytes | None:
        context = await self._ensure_context()
        response = await context.request.fetch(
            url,
            method="GET",
            headers={"Range": f"bytes=0-{max_bytes - 1}"},
            timeout=self._settings.playwright.timeout,
        )
        if response.status >= 400:
            return None
        body = await response.body()
        return body[:max_bytes] if body else None

    async def download_file(
        self,
        url: str,
        dest: Path,
        referer: str | None = None,
    ) -> DownloadResult:
        context = await self._ensure_context()
        headers: dict[str, str] = {}
        if referer:
            headers["Referer"] = referer

        response = await context.request.fetch(
            url,
            method="GET",
            headers=headers,
            timeout=self._settings.playwright.timeout,
        )
        if response.status >= 400:
            raise ValueError(f"Download request failed with status {response.status}")

        body = await response.body()
        if body is None:
            raise ValueError("Empty response body")
        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, "wb") as f:
            f.write(body)
        normalized_headers = {k.lower(): v for k, v in response.headers.items()}
        return DownloadResult(
            size=len(body),
            status_code=response.status,
            headers=normalized_headers,
        )

    @staticmethod
    def _extract_content_length(response: APIResponse) -> int | None:
        if response.status >= 400:
            return None
        for key, value in response.headers.items():
            if key.lower() == "content-length" and str(value).isdigit():
                return int(value)
        return None

    async def close(self) -> None:
        if self._context:
            await self._context.close()
            self._context = None
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
