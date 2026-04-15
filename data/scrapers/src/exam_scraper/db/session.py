from __future__ import annotations

import aiosqlite
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS crawled_urls (
    url_hash TEXT PRIMARY KEY,
    url TEXT NOT NULL,
    domain TEXT NOT NULL,
    has_pdf INTEGER DEFAULT 0,
    crawled_at TEXT DEFAULT (datetime('now')),
    ttl_days INTEGER DEFAULT 7
);

CREATE INDEX IF NOT EXISTS idx_crawled_domain ON crawled_urls(domain);

CREATE TABLE IF NOT EXISTS exam_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_url TEXT NOT NULL,
    source_domain TEXT NOT NULL,
    pdf_url TEXT NOT NULL,
    local_path TEXT NOT NULL,
    file_hash TEXT UNIQUE,
    file_size_bytes INTEGER,
    title TEXT,
    grade TEXT,
    subject TEXT,
    exam_type TEXT,
    year INTEGER,
    province TEXT,
    parse_status TEXT DEFAULT 'pending',
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_exam_year ON exam_documents(year DESC);
CREATE INDEX IF NOT EXISTS idx_exam_parse ON exam_documents(parse_status);
CREATE INDEX IF NOT EXISTS idx_exam_grade ON exam_documents(grade, subject);
"""


async def get_db(db_path: Path) -> aiosqlite.Connection:
    db = await aiosqlite.connect(str(db_path))
    db.row_factory = aiosqlite.Row
    await db.executescript(SCHEMA)
    await db.commit()
    return db
