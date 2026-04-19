from pathlib import Path

import pytest

from exam_scraper.core import Downloader, PdfValidationError


class _DownloadResult:
    def __init__(self, size: int, headers: dict[str, str]):
        self.size = size
        self.headers = headers
        self.status_code = 200


class _ClientStub:
    def __init__(self, payload: bytes, headers: dict[str, str] | None = None):
        self._payload = payload
        self._headers = headers or {"content-type": "application/pdf"}

    async def download_file(self, url: str, dest: Path, referer: str | None = None):
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(self._payload)
        return _DownloadResult(size=len(self._payload), headers=self._headers)


@pytest.mark.asyncio
async def test_downloader_rejects_invalid_magic_bytes(tmp_path):
    client = _ClientStub(payload=b"NOT_A_PDF" * 300)
    downloader = Downloader(client)
    out = tmp_path / "bad.pdf"

    with pytest.raises(PdfValidationError):
        await downloader.download("https://example.com/file.pdf", out)

    assert not out.exists()


@pytest.mark.asyncio
async def test_downloader_requires_network_signal_when_configured(tmp_path):
    client = _ClientStub(
        payload=b"%PDF-1.7\n" + b"A" * 2048,
        headers={"content-type": "text/html"},
    )
    downloader = Downloader(client)
    out = tmp_path / "bad-signal.pdf"

    with pytest.raises(PdfValidationError):
        await downloader.download(
            "https://example.com/download",
            out,
            require_network_signal=True,
        )

    assert not out.exists()


@pytest.mark.asyncio
async def test_downloader_accepts_valid_pdf(tmp_path):
    client = _ClientStub(payload=b"%PDF-1.7\n" + b"A" * 4096)
    downloader = Downloader(client)
    out = tmp_path / "ok.pdf"

    dest, file_hash, size = await downloader.download("https://example.com/file.pdf", out)

    assert dest.exists()
    assert len(file_hash) == 64
    assert size > 1024
