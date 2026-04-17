from __future__ import annotations

import asyncio
import random
from functools import partial
import httpx
import cloudscraper
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from exam_scraper.config import Settings
from exam_scraper.utils.ua_pool import get_headers

logger = structlog.get_logger()


class HttpClient:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._async_client: httpx.AsyncClient | None = None
        self._scraper = cloudscraper.create_scraper(
            browser={"browser": "chrome", "platform": "windows"}
        )

    async def _get_client(self) -> httpx.AsyncClient:
        if self._async_client is None:
            self._async_client = httpx.AsyncClient(
                follow_redirects=True,
                timeout=30.0,
                limits=httpx.Limits(max_connections=10),
            )
        return self._async_client

    async def _throttle(self) -> None:
        delay = random.uniform(
            self._settings.throttle.min_delay,
            self._settings.throttle.max_delay,
        )
        await asyncio.sleep(delay)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.ConnectError)),
    )
    async def fetch(self, url: str) -> httpx.Response:
        await self._throttle()
        client = await self._get_client()
        headers = get_headers()
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        logger.debug("fetched", url=url, status=response.status_code)
        return response

    def fetch_sync(self, url: str) -> str:
        headers = get_headers()
        response = self._scraper.get(url, headers=headers)
        response.raise_for_status()
        return response.text

    async def fetch_with_cloudscraper(self, url: str) -> str:
        await self._throttle()
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.fetch_sync, url)

    def _head_sync(self, url: str) -> int | None:
        headers = get_headers()
        try:
            response = self._scraper.head(url, headers=headers, allow_redirects=True)
            response.raise_for_status()
            content_length = response.headers.get("Content-Length")
            if content_length and content_length.isdigit():
                return int(content_length)
            return None
        except Exception as e:
            logger.debug("head_request_failed", error=str(e), url=url)
            return None

    async def head_file_size(self, url: str) -> int | None:
        await self._throttle()
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._head_sync, url)

    def _fetch_file_header_sync(self, url: str, max_bytes: int) -> bytes | None:
        headers = get_headers()
        headers["Range"] = f"bytes=0-{max_bytes - 1}"
        try:
            response = self._scraper.get(url, headers=headers, allow_redirects=True)
            response.raise_for_status()
            return response.content[:max_bytes] if response.content else None
        except Exception as e:
            logger.debug("header_fetch_failed", error=str(e), url=url)
            return None

    async def fetch_file_header(self, url: str, max_bytes: int = 65536) -> bytes | None:
        await self._throttle()
        loop = asyncio.get_event_loop()
        fn = partial(self._fetch_file_header_sync, url, max_bytes)
        return await loop.run_in_executor(None, fn)

    async def download_file(self, url: str, dest: str) -> int:
        await self._throttle()
        client = await self._get_client()
        headers = get_headers()
        async with client.stream("GET", url, headers=headers) as response:
            response.raise_for_status()
            total = 0
            with open(dest, "wb") as f:
                async for chunk in response.aiter_bytes(8192):
                    f.write(chunk)
                    total += len(chunk)
        return total

    async def close(self) -> None:
        if self._async_client:
            await self._async_client.aclose()
            self._async_client = None
