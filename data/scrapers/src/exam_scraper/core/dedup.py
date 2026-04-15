from __future__ import annotations

import aiosqlite
from datetime import datetime, timedelta

from exam_scraper.utils.url_utils import normalize_url, url_hash, extract_domain


class DedupCache:
    def __init__(self, db: aiosqlite.Connection, ttl_days: int = 7):
        self._db = db
        self._ttl_days = ttl_days

    async def is_crawled(self, url: str) -> bool:
        h = url_hash(url)
        cursor = await self._db.execute(
            "SELECT crawled_at, ttl_days FROM crawled_urls WHERE url_hash = ?",
            (h,),
        )
        row = await cursor.fetchone()
        if row is None:
            return False
        crawled_at = datetime.fromisoformat(row["crawled_at"])
        ttl = timedelta(days=row["ttl_days"])
        return datetime.utcnow() - crawled_at < ttl

    async def mark_crawled(
        self, url: str, has_pdf: bool = False, commit: bool = True
    ) -> None:
        h = url_hash(url)
        await self._db.execute(
            """INSERT OR REPLACE INTO crawled_urls
               (url_hash, url, domain, has_pdf, ttl_days)
               VALUES (?, ?, ?, ?, ?)""",
            (h, normalize_url(url), extract_domain(url), int(has_pdf), self._ttl_days),
        )
        if commit:
            await self._db.commit()

    async def clear(self, domain: str | None = None) -> int:
        if domain:
            cursor = await self._db.execute(
                "DELETE FROM crawled_urls WHERE domain = ?", (domain,)
            )
        else:
            cursor = await self._db.execute("DELETE FROM crawled_urls")
        await self._db.commit()
        return cursor.rowcount

    async def stats(self) -> dict:
        cursor = await self._db.execute(
            "SELECT domain, COUNT(*) as cnt FROM crawled_urls GROUP BY domain"
        )
        rows = await cursor.fetchall()
        total = sum(r["cnt"] for r in rows)
        return {
            "total": total,
            "by_domain": {r["domain"]: r["cnt"] for r in rows},
        }
