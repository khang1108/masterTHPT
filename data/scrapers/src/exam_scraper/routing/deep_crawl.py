from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Type
from urllib.parse import parse_qs, unquote, urlparse
from urllib.parse import urldefrag
from uuid import uuid4
import re

import aiosqlite
import structlog

from exam_scraper.config import Settings
from exam_scraper.core.crawl_transaction import CrawlTransaction
from exam_scraper.core.dedup import DedupCache
from exam_scraper.core.detectors import DownloadTargetDetector
from exam_scraper.core.downloader import Downloader, PdfValidationError
from exam_scraper.core.pdf_extractor import PdfExtractor
from exam_scraper.core.playwright_crawler import CapturedPdfUrl, PlaywrightCrawlerClient
from exam_scraper.db.models import ExamDocument
from exam_scraper.db.session import get_db
from exam_scraper.spiders.base_spider import BaseSpider
from exam_scraper.utils.file_utils import (
    build_pdf_filename,
    build_pdf_path,
    ensure_unique_path,
)
from exam_scraper.utils.url_utils import canonicalize_subject, extract_subject

logger = structlog.get_logger()


class DeepCrawlRouter:
    HEADER_COMPARE_BYTES = 64 * 1024

    def __init__(self, settings: Settings):
        self._settings = settings

    def _to_abs_path(self, local_path: str) -> Path:
        p = Path(local_path)
        if p.is_absolute():
            return p
        return self._settings.storage_path.parent / p

    @staticmethod
    def _header_hash(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    def _local_header_hash(
        self, path: Path, max_bytes: int = HEADER_COMPARE_BYTES
    ) -> str | None:
        if not path.exists() or not path.is_file():
            return None
        with open(path, "rb") as f:
            chunk = f.read(max_bytes)
        if not chunk:
            return None
        return self._header_hash(chunk)

    async def _is_duplicate_by_size_and_header(
        self,
        db: aiosqlite.Connection,
        http,
        pdf_url: str,
        content_length: int | None,
    ) -> bool:
        if not content_length or content_length <= 1024:
            return False

        cur = await db.execute(
            "SELECT local_path FROM exam_documents WHERE file_size_bytes = ?",
            (content_length,),
        )
        rows = await cur.fetchall()
        if not rows:
            return False

        remote_header = await http.fetch_file_header(pdf_url, self.HEADER_COMPARE_BYTES)
        if not remote_header:
            return False
        remote_header_hash = self._header_hash(remote_header)

        for row in rows:
            local_path = self._to_abs_path(row["local_path"])
            local_header_hash = self._local_header_hash(
                local_path, self.HEADER_COMPARE_BYTES
            )
            if local_header_hash and local_header_hash == remote_header_hash:
                logger.info(
                    "skip_duplicate_size_and_header",
                    size=content_length,
                    local_path=str(local_path),
                    url=pdf_url,
                )
                return True
        return False

    async def _hash_exists(self, db: aiosqlite.Connection, file_hash: str) -> bool:
        cur = await db.execute(
            "SELECT 1 FROM exam_documents WHERE file_hash = ?", (file_hash,)
        )
        return await cur.fetchone() is not None

    @staticmethod
    def _looks_like_pdf_candidate(url: str) -> bool:
        parsed = urlparse(url)
        path = parsed.path.lower()
        if path.endswith(".pdf"):
            return True
        for key in ("file", "url", "src", "download"):
            for value in parse_qs(parsed.query).get(key, []):
                if ".pdf" in unquote(value).lower():
                    return True
        return False

    @staticmethod
    def _is_explorable_url(url: str) -> bool:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            return False
        path = parsed.path.lower()
        if path in {"", "/"}:
            return False
        if any(
            path.endswith(ext)
            for ext in (
                ".jpg",
                ".jpeg",
                ".png",
                ".gif",
                ".svg",
                ".css",
                ".js",
                ".ico",
                ".woff",
                ".woff2",
                ".zip",
                ".rar",
                ".doc",
                ".docx",
                ".xls",
                ".xlsx",
                ".ppt",
                ".pptx",
            )
        ):
            return False
        blocked = (
            "/wp-admin",
            "/wp-login",
            "/login",
            "/register",
            "/gioi-thieu",
            "/lien-he",
            "/privacy",
            "/policy",
        )
        if any(token in path for token in blocked):
            return False
        return True

    @staticmethod
    def _extract_grade_from_url(url: str) -> str | None:
        combined = unquote(url).lower()
        if re.search(r"(lop|khoi)[-_ ]*10|\b10\b", combined):
            return "10"
        if re.search(r"(lop|khoi)[-_ ]*11|\b11\b", combined):
            return "11"
        if re.search(r"(lop|khoi)[-_ ]*12|\b12\b", combined):
            return "12"
        if "thpt" in combined or "tot-nghiep" in combined or "tot nghiep" in combined:
            return "thpt"
        return None

    @staticmethod
    def _extract_exam_type_from_url(url: str) -> str | None:
        combined = unquote(url).lower()
        if any(k in combined for k in ("giua-hk1", "giua-ky-1", "giua ki 1", "giua hoc ky 1")):
            return "giua_hk1"
        if any(k in combined for k in ("hk1", "hoc-ky-1", "hoc ky 1", "ki-1")):
            return "hk1"
        if any(k in combined for k in ("giua-hk2", "giua-ky-2", "giua ki 2", "giua hoc ky 2")):
            return "giua_hk2"
        if any(k in combined for k in ("hk2", "hoc-ky-2", "hoc ky 2", "ki-2")):
            return "hk2"
        if "thi-thu" in combined or "thi thu" in combined:
            return "thi_thu"
        if "de-cuong" in combined or "de cuong" in combined:
            return "de_cuong"
        return None

    @staticmethod
    def _extract_subject_from_url(url: str) -> str | None:
        combined = canonicalize_subject(extract_subject("", unquote(url).lower()))
        return combined if combined != "unknown" else None

    def _link_priority(
        self,
        url: str,
        allowed_subjects: set[str] | None,
        grade_filter: str | None,
        exam_type_filter: str | None,
        seed_tokens: set[str] | None = None,
    ) -> float:
        score = 0.0
        path = urlparse(url).path.lower()
        if "/chuyen-muc/" in path or "/tag/" in path or "/category/" in path:
            score += 3.0
        if "/page/" in path:
            score += 0.5
        if self._looks_like_pdf_candidate(url):
            score -= 2.0

        subject = self._extract_subject_from_url(url)
        grade = self._extract_grade_from_url(url)
        exam_type = self._extract_exam_type_from_url(url)

        if allowed_subjects:
            if subject and subject in allowed_subjects:
                score += 8.0
            elif subject and subject not in allowed_subjects:
                score -= 4.0
        if grade_filter:
            if grade == grade_filter:
                score += 6.0
            elif grade and grade != grade_filter:
                score -= 3.0
        if exam_type_filter:
            if exam_type == exam_type_filter:
                score += 5.0
            elif exam_type and exam_type != exam_type_filter:
                score -= 2.5
        if seed_tokens:
            tokens = set(re.findall(r"[a-z0-9]{3,}", unquote(path)))
            overlap = len(tokens & seed_tokens)
            score += overlap * 1.5
        return score

    @staticmethod
    def _merge_pdf_urls(info_urls: list[str], captured: list[CapturedPdfUrl]) -> list[str]:
        merged: list[str] = []
        seen: set[str] = set()
        for url in info_urls + [item.url for item in captured]:
            if not url or url in seen:
                continue
            seen.add(url)
            merged.append(url)
        return merged

    @staticmethod
    def _build_signal_map(captured: list[CapturedPdfUrl]) -> dict[str, bool]:
        out: dict[str, bool] = {}
        for item in captured:
            out[item.url] = out.get(item.url, False) or item.has_network_pdf_signal()
        return out

    async def run(
        self,
        spider_cls: Type[BaseSpider],
        start_url: str,
        limit: int = 0,
        min_year: int = 0,
        allowed_subjects: set[str] | None = None,
        grade_filter: str | None = None,
        exam_type_filter: str | None = None,
    ) -> int:
        spider = spider_cls()
        logger.info("start_deep_crawl", domain=spider.domain, tier=spider.tier)

        db = await get_db(self._settings.db_path)
        cache = DedupCache(db, self._settings.dedup.ttl_days)
        crawler = PlaywrightCrawlerClient(self._settings)
        downloader = Downloader(crawler)
        detector = DownloadTargetDetector(self._settings.detectors)
        extractor = PdfExtractor()
        pending_cache_marks: list[tuple[str, bool]] = []

        temp_run_dir = (
            self._settings.storage_path
            / ".tmp_runs"
            / f"run_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}"
        )
        tx = CrawlTransaction(db=db, temp_dir=temp_run_dir)

        downloaded = 0
        visited_in_run: set[str] = set()
        stack: list[tuple[str, int]] = [(start_url, 0)]
        pages_processed = 0
        seed_tokens = set(re.findall(r"[a-z0-9]{3,}", unquote(urlparse(start_url).path.lower())))
        seed_tokens -= {"chuyen", "muc", "page", "html", "php", "de", "thi", "lop", "mon"}

        try:
            await tx.begin()
            while stack:
                if limit > 0 and downloaded >= limit:
                    break
                if pages_processed >= self._settings.crawl.max_pages:
                    logger.info(
                        "max_pages_reached",
                        max_pages=self._settings.crawl.max_pages,
                        downloaded=downloaded,
                    )
                    break

                link, depth = stack.pop()
                link = urldefrag(link)[0]
                if depth > self._settings.crawl.max_depth:
                    continue
                if link in visited_in_run:
                    continue
                visited_in_run.add(link)
                pages_processed += 1

                if not spider.matches(link):
                    continue
                if depth > 0 and not self._is_explorable_url(link):
                    continue

                if await cache.is_crawled(link):
                    logger.debug("skip_cached", url=link, depth=depth)
                    continue

                page_html, captured_urls = await crawler.detect_pdf_urls(
                    link, detector=detector, extractor=extractor
                )
                signal_map = self._build_signal_map(captured_urls)

                child_links = spider.parse_listing_page(page_html, link)
                ranked_children: list[tuple[float, str]] = []
                for child in child_links:
                    child = urldefrag(child)[0]
                    if child in visited_in_run:
                        continue
                    if not spider.matches(child) or not self._is_explorable_url(child):
                        continue
                    ranked_children.append(
                        (
                            self._link_priority(
                                child,
                                allowed_subjects=allowed_subjects,
                                grade_filter=grade_filter,
                                exam_type_filter=exam_type_filter,
                                seed_tokens=seed_tokens,
                            ),
                            child,
                        )
                    )
                ranked_children.sort(key=lambda item: item[0], reverse=True)
                for _, child in reversed(ranked_children):
                    stack.append((child, depth + 1))

                info = spider.parse_detail_page(page_html, link)
                info.pdf_urls = self._merge_pdf_urls(info.pdf_urls, captured_urls)

                detected_subject = (
                    canonicalize_subject(info.subject) if info.subject else "unknown"
                )
                if detected_subject == "unknown":
                    detected_subject = canonicalize_subject(
                        extract_subject(info.title or "", link)
                    )
                info.subject = detected_subject

                if min_year and info.year and info.year < min_year:
                    logger.debug("skip_old_year", year=info.year, min_year=min_year)
                    pending_cache_marks.append((link, False))
                    continue

                if allowed_subjects and info.subject not in allowed_subjects:
                    logger.debug(
                        "skip_subject_not_selected",
                        subject=info.subject,
                        allowed_subjects=sorted(allowed_subjects),
                        url=link,
                    )
                    pending_cache_marks.append((link, False))
                    continue

                if grade_filter and (info.grade or "") != grade_filter:
                    logger.debug(
                        "skip_grade_not_selected",
                        grade=info.grade,
                        grade_filter=grade_filter,
                        url=link,
                    )
                    pending_cache_marks.append((link, False))
                    continue

                if exam_type_filter and (info.exam_type or "") != exam_type_filter:
                    logger.debug(
                        "skip_exam_type_not_selected",
                        exam_type=info.exam_type,
                        exam_type_filter=exam_type_filter,
                        url=link,
                    )
                    pending_cache_marks.append((link, False))
                    continue

                if not info.pdf_urls:
                    pending_cache_marks.append((link, False))
                    continue

                downloaded_this_link = False
                had_duplicate = False

                for pdf_url in info.pdf_urls:
                    if not self._looks_like_pdf_candidate(pdf_url):
                        logger.debug("skip_non_pdf_candidate", url=pdf_url, detail=link)
                        continue

                    dest_dir = build_pdf_path(
                        self._settings.storage_path,
                        spider.domain,
                        info.grade or "unknown",
                        info.subject or "unknown",
                        info.exam_type or "unknown",
                    )
                    filename = build_pdf_filename(
                        info.grade or "unknown",
                        info.subject or "unknown",
                        info.exam_type or "unknown",
                        spider.domain,
                        school=info.province or "",
                    )

                    content_length = await crawler.head_file_size(pdf_url)
                    if await self._is_duplicate_by_size_and_header(
                        db=db,
                        http=crawler,
                        pdf_url=pdf_url,
                        content_length=content_length,
                    ):
                        had_duplicate = True
                        continue

                    final_dest = ensure_unique_path(dest_dir / filename)
                    temp_dest = tx.build_temp_path(final_dest.name)

                    require_network_signal = signal_map.get(pdf_url, False)
                    try:
                        tmp_path, file_hash, size = await downloader.download(
                            pdf_url,
                            temp_dest,
                            referer=link,
                            require_network_signal=require_network_signal,
                        )
                    except PdfValidationError as e:
                        logger.warning(
                            "skip_invalid_pdf_candidate",
                            url=pdf_url,
                            detail=link,
                            error=str(e),
                        )
                        continue

                    if await self._hash_exists(db, file_hash):
                        tmp_path.unlink(missing_ok=True)
                        logger.info(
                            "skip_duplicate_hash", hash=file_hash[:12], url=pdf_url
                        )
                        had_duplicate = True
                        continue

                    final_dest.parent.mkdir(parents=True, exist_ok=True)
                    tmp_path.replace(final_dest)
                    tx.register_final_file(final_dest)

                    doc = ExamDocument(
                        source_url=link,
                        source_domain=spider.domain,
                        pdf_url=pdf_url,
                        local_path=str(
                            final_dest.relative_to(self._settings.storage_path.parent)
                        ),
                        file_hash=file_hash,
                        file_size_bytes=size,
                        title=info.title,
                        grade=info.grade,
                        subject=info.subject,
                        exam_type=info.exam_type,
                        year=info.year,
                    )

                    await db.execute(
                        """INSERT INTO exam_documents
                           (source_url, source_domain, pdf_url, local_path, file_hash, file_size_bytes,
                            title, grade, subject, exam_type, year)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            doc.source_url,
                            doc.source_domain,
                            doc.pdf_url,
                            doc.local_path,
                            doc.file_hash,
                            doc.file_size_bytes,
                            doc.title,
                            doc.grade,
                            doc.subject,
                            doc.exam_type,
                            doc.year,
                        ),
                    )

                    downloaded += 1
                    downloaded_this_link = True
                    break

                pending_cache_marks.append((link, downloaded_this_link or had_duplicate))
            
            await tx.commit()
            for url, has_pdf in pending_cache_marks:
                await cache.mark_crawled(url, has_pdf=has_pdf, commit=False)
            await db.commit()

            logger.info("deep_crawl_complete", downloaded=downloaded)
            return downloaded

        except Exception as e:
            logger.error("crawl_failed_abort", error=str(e), downloaded=downloaded)
            await tx.rollback()
            raise
        finally:
            await crawler.close()
            await db.close()
