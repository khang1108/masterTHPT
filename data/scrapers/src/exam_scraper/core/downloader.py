from __future__ import annotations

import structlog
from pathlib import Path

from exam_scraper.utils.file_utils import file_sha256, ensure_unique_path

logger = structlog.get_logger()


class PdfValidationError(ValueError):
    pass


class Downloader:
    def __init__(self, client, min_pdf_size: int = 1024):
        self._client = client
        self._min_pdf_size = min_pdf_size

    @staticmethod
    def _looks_like_pdf_headers(url: str, headers: dict[str, str]) -> bool:
        lower_headers = {k.lower(): v.lower() for k, v in headers.items()}
        content_type = lower_headers.get("content-type", "")
        content_disp = lower_headers.get("content-disposition", "")
        url_lower = url.lower()
        return (
            ".pdf" in url_lower
            or "application/pdf" in content_type
            or (".pdf" in content_disp and "filename" in content_disp)
        )

    def _validate_pdf_file(
        self,
        path: Path,
        size: int,
        url: str,
        headers: dict[str, str],
        require_network_signal: bool,
    ) -> None:
        if size < self._min_pdf_size:
            raise PdfValidationError(
                f"File too small ({size}B), likely not a valid PDF"
            )

        with open(path, "rb") as f:
            header = f.read(8)
        if not header.startswith(b"%PDF-"):
            raise PdfValidationError("Invalid PDF magic bytes")

        if require_network_signal and not self._looks_like_pdf_headers(url, headers):
            raise PdfValidationError("Missing PDF network/header signal")

    async def download(
        self,
        url: str,
        dest: Path,
        referer: str | None = None,
        require_network_signal: bool = False,
    ) -> tuple[Path, str, int]:
        dest = ensure_unique_path(dest)
        result = await self._client.download_file(url, dest, referer=referer)
        try:
            self._validate_pdf_file(
                path=dest,
                size=result.size,
                url=url,
                headers=result.headers,
                require_network_signal=require_network_signal,
            )
        except PdfValidationError:
            dest.unlink(missing_ok=True)
            raise
        hash_val = file_sha256(dest)
        logger.info("downloaded", path=str(dest), size=result.size, hash=hash_val[:12])
        return dest, hash_val, result.size

    async def download_if_new(
        self,
        url: str,
        dest: Path,
        known_hashes: set[str],
        referer: str | None = None,
        require_network_signal: bool = False,
    ) -> tuple[Path, str, int] | None:
        dest = ensure_unique_path(dest)
        result = await self._client.download_file(url, dest, referer=referer)
        try:
            self._validate_pdf_file(
                path=dest,
                size=result.size,
                url=url,
                headers=result.headers,
                require_network_signal=require_network_signal,
            )
        except PdfValidationError:
            dest.unlink(missing_ok=True)
            return None
        hash_val = file_sha256(dest)
        if hash_val in known_hashes:
            dest.unlink(missing_ok=True)
            logger.debug("duplicate_skipped", url=url, hash=hash_val[:12])
            return None
        logger.info("downloaded", path=str(dest), size=result.size)
        return dest, hash_val, result.size
