from __future__ import annotations

import structlog
from playwright.async_api import async_playwright, Page, Browser

from exam_scraper.config import Settings

logger = structlog.get_logger()


class BrowserClient:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._browser: Browser | None = None
        self._playwright = None

    async def _ensure_browser(self) -> Browser:
        if self._browser is None:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=self._settings.playwright.headless,
            )
            logger.info("browser_launched")
        return self._browser

    async def get_page(self) -> Page:
        browser = await self._ensure_browser()
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="vi-VN",
        )
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

    async def close(self) -> None:
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
