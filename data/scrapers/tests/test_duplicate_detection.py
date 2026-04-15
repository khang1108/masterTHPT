import pytest

from exam_scraper.config import Settings
from exam_scraper.db.session import get_db
from exam_scraper.routing.deep_crawl import DeepCrawlRouter


class _HttpStub:
    def __init__(self, payload: bytes | None):
        self._payload = payload

    async def fetch_file_header(self, url: str, max_bytes: int = 65536) -> bytes | None:
        if self._payload is None:
            return None
        return self._payload[:max_bytes]


@pytest.mark.asyncio
async def test_duplicate_detected_by_size_and_header(tmp_path):
    settings = Settings(storage_dir=str(tmp_path / "storage"), data_dir=str(tmp_path / "data"))
    router = DeepCrawlRouter(settings)
    db = await get_db(settings.db_path)

    try:
        content = b"%PDF-1.7\n" + (b"A" * 4096)
        file_path = settings.storage_path / "toanmath.com" / "lop-12" / "toan" / "unknown" / "sample.pdf"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(content)

        await db.execute(
            """INSERT INTO exam_documents
               (source_url, source_domain, pdf_url, local_path, file_hash, file_size_bytes)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                "https://toanmath.com/de-1",
                "toanmath.com",
                "https://toanmath.com/files/de-1.pdf",
                str(file_path.relative_to(settings.storage_path.parent)),
                "hash-existing-1",
                len(content),
            ),
        )
        await db.commit()

        http = _HttpStub(content)
        is_dup = await router._is_duplicate_by_size_and_header(
            db=db,
            http=http,  # type: ignore[arg-type]
            pdf_url="https://example.com/new.pdf",
            content_length=len(content),
        )

        assert is_dup is True
    finally:
        await db.close()


@pytest.mark.asyncio
async def test_not_duplicate_when_header_differs_even_if_size_matches(tmp_path):
    settings = Settings(storage_dir=str(tmp_path / "storage"), data_dir=str(tmp_path / "data"))
    router = DeepCrawlRouter(settings)
    db = await get_db(settings.db_path)

    try:
        local_content = b"%PDF-1.7\n" + (b"L" * 4096)
        remote_content = b"%PDF-1.7\n" + (b"R" * 4096)
        assert len(local_content) == len(remote_content)

        file_path = settings.storage_path / "thi247.com" / "lop-11" / "toan" / "unknown" / "sample.pdf"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(local_content)

        await db.execute(
            """INSERT INTO exam_documents
               (source_url, source_domain, pdf_url, local_path, file_hash, file_size_bytes)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                "https://thi247.com/de-2",
                "thi247.com",
                "https://thi247.com/files/de-2.pdf",
                str(file_path.relative_to(settings.storage_path.parent)),
                "hash-existing-2",
                len(local_content),
            ),
        )
        await db.commit()

        http = _HttpStub(remote_content)
        is_dup = await router._is_duplicate_by_size_and_header(
            db=db,
            http=http,  # type: ignore[arg-type]
            pdf_url="https://example.com/new.pdf",
            content_length=len(remote_content),
        )

        assert is_dup is False
    finally:
        await db.close()
