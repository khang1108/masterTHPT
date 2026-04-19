import pytest

from exam_scraper.config import Settings
from exam_scraper.core import CrawlTransaction
from exam_scraper.core import get_db


@pytest.mark.asyncio
async def test_transaction_rollback_removes_files_and_db_rows(tmp_path):
    settings = Settings(
        storage_dir=str(tmp_path / "storage" / "pdfs"),
        data_dir=str(tmp_path / "storage" / "state"),
    )
    db = await get_db(settings.db_path)
    temp_dir = settings.data_path / ".tmp_runs" / "run_test"
    tx = CrawlTransaction(db, temp_dir)

    final_file = settings.storage_path / "toan" / "lop-12" / "x.pdf"
    final_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        await tx.begin()
        final_file.write_bytes(b"%PDF-1.7\n" + b"A" * 2048)
        tx.register_final_file(final_file)
        await db.execute(
            """INSERT INTO exam_documents
               (source_url, source_domain, pdf_url, local_path)
               VALUES (?, ?, ?, ?)""",
            (
                "https://toanmath.com/detail",
                "toanmath.com",
                "https://toanmath.com/a.pdf",
                str(final_file.resolve()),
            ),
        )

        await tx.rollback()

        cur = await db.execute("SELECT COUNT(*) as c FROM exam_documents")
        row = await cur.fetchone()
        assert row["c"] == 0
        assert not final_file.exists()
        assert not temp_dir.exists()
    finally:
        await db.close()
