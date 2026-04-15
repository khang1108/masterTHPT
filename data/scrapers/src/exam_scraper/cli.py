from __future__ import annotations

import typer
import asyncio
from datetime import datetime
import json
import structlog
from pathlib import Path

from exam_scraper.config import Settings
from exam_scraper.db.session import get_db
from exam_scraper.utils.query_intent import QueryIntentParser
from exam_scraper.utils.url_utils import canonicalize_subject

logger = structlog.get_logger()
app = typer.Typer(help="Core Exam PDF Scraper")


def _get_spider(domain: str):
    from exam_scraper.spiders.toanmath import ToanMathSpider
    from exam_scraper.spiders.thi247 import Thi247Spider
    from exam_scraper.spiders.doctailieu import DocTaiLieuSpider
    from exam_scraper.spiders.hoc247 import Hoc247Spider
    from exam_scraper.spiders.vietjack import VietJackSpider
    from exam_scraper.spiders.generic import GenericSpider

    spiders = {
        "toanmath.com": ToanMathSpider,
        "thi247.com": Thi247Spider,
        "doctailieu.com": DocTaiLieuSpider,
        "hoc247.net": Hoc247Spider,
        "vietjack.com": VietJackSpider,
    }
    return spiders.get(domain.lower(), GenericSpider)


@app.command()
def crawl(
    domain: str = typer.Option(..., help="Domain to crawl (e.g. toanmath.com)"),
    start_url: str = typer.Option(None, help="Start URL to extract links from"),
    grade: str = typer.Option(None, help="Grade to filter"),
    subject: str = typer.Option(None, help="Subject to filter"),
    exam_type: str = typer.Option(None, "--exam-type", help="Exam type to filter"),
    query: str = typer.Option(None, "--query", help="Natural language query for subject/grade/exam type"),
    limit: int = typer.Option(10, help="Maximum PDFs to download"),
    min_year: int = typer.Option(2022, help="Minimum year of exam to keep"),
    force: bool = typer.Option(False, help="Bypass URL dedup cache"),
    tier: str = typer.Option(None, help="Spider tier to force, e.g T3"),
    auto_discover: bool = typer.Option(False, "--auto-discover", help="Fallback to known good domains if 0 found"),
    toan: bool = typer.Option(False, "--toan", help="Only crawl Toan"),
    ngu_van: bool = typer.Option(False, "--ngu_van", help="Only crawl Ngu van"),
    tieng_anh: bool = typer.Option(False, "--tieng_anh", help="Only crawl Tieng Anh"),
    vat_ly: bool = typer.Option(False, "--vat_ly", help="Only crawl Vat ly"),
    hoa_hoc: bool = typer.Option(False, "--hoa_hoc", help="Only crawl Hoa hoc"),
    sinh_hoc: bool = typer.Option(False, "--sinh_hoc", help="Only crawl Sinh hoc"),
    lich_su: bool = typer.Option(False, "--lich_su", help="Only crawl Lich su"),
    dia_ly: bool = typer.Option(False, "--dia_ly", help="Only crawl Dia ly"),
    gdcd: bool = typer.Option(False, "--gdcd", help="Only crawl GDCD"),
    gdktpl: bool = typer.Option(False, "--gdktpl", help="Only crawl GDKTPL"),
    tin_hoc: bool = typer.Option(False, "--tin_hoc", help="Only crawl Tin hoc"),
    cong_nghe: bool = typer.Option(False, "--cong_nghe", help="Only crawl Cong nghe"),
):
    """Deep crawl a specific domain using its associated Spider."""
    from exam_scraper.routing.deep_crawl import DeepCrawlRouter
    
    settings = Settings.from_yaml()
    if not start_url:
        start_url = f"https://{domain}"
        
    spider_cls = _get_spider(domain)
    
    if force:
        async def clear_cache():
            db = await get_db(settings.db_path)
            await db.execute("DELETE FROM crawled_urls WHERE domain = ?", (domain,))
            await db.commit()
            await db.close()
        asyncio.run(clear_cache())
        logger.info("cache_cleared", domain=domain)
        
    router = DeepCrawlRouter(settings)
    parser = QueryIntentParser(settings.detectors.intent)
    intent = parser.parse(query)

    selected_subjects = set()
    if toan:
        selected_subjects.add("toan")
    if ngu_van:
        selected_subjects.add("van")
    if tieng_anh:
        selected_subjects.add("anh")
    if vat_ly:
        selected_subjects.add("ly")
    if hoa_hoc:
        selected_subjects.add("hoa")
    if sinh_hoc:
        selected_subjects.add("sinh")
    if lich_su:
        selected_subjects.add("su")
    if dia_ly:
        selected_subjects.add("dia")
    if gdcd:
        selected_subjects.add("gdcd")
    if gdktpl:
        selected_subjects.add("gdktpl")
    if tin_hoc:
        selected_subjects.add("tin")
    if cong_nghe:
        selected_subjects.add("cong_nghe")
    explicit_subject = canonicalize_subject(subject) if subject else None
    if explicit_subject and explicit_subject != "unknown":
        selected_subjects.add(explicit_subject)

    query_subject = canonicalize_subject(intent.subject) if intent.subject else None
    if selected_subjects and query_subject and query_subject not in selected_subjects:
        logger.warning(
            "query_conflict_subject_ignored",
            query_subject=query_subject,
            explicit_subjects=sorted(selected_subjects),
        )
    allowed_subjects = selected_subjects or ({query_subject} if query_subject else None)

    grade_filter = grade or intent.grade
    if grade and intent.grade and grade != intent.grade:
        logger.warning("query_conflict_grade_ignored", query_grade=intent.grade, explicit_grade=grade)

    exam_type_filter = exam_type or intent.exam_type
    if exam_type and intent.exam_type and exam_type != intent.exam_type:
        logger.warning(
            "query_conflict_exam_type_ignored",
            query_exam_type=intent.exam_type,
            explicit_exam_type=exam_type,
        )

    async def _run_routing():
        d = domain
        u = start_url
        downloaded = await router.run(
            _get_spider(d),
            u,
            limit,
            min_year,
            allowed_subjects=allowed_subjects,
            grade_filter=grade_filter,
            exam_type_filter=exam_type_filter,
        )
        
        if downloaded == 0 and auto_discover:
            logger.info("auto_discover_triggered", reason="0 PDFs yielded", initial_domain=d)
            fallback_queue = ["thitotnghiepthpt.vn", "toanmath.com", "tailieudieuky.com"]
            for fbd in fallback_queue:
                if fbd == d: continue
                logger.info("auto_discover_fallback", trying=fbd)
                downloaded = await router.run(
                    _get_spider(fbd),
                    f"https://{fbd}",
                    limit,
                    min_year,
                    allowed_subjects=allowed_subjects,
                    grade_filter=grade_filter,
                    exam_type_filter=exam_type_filter,
                )
                if downloaded > 0:
                    logger.info("auto_discover_success", found_on=fbd, count=downloaded)
                    break
                    
    try:
        asyncio.run(_run_routing())
    except Exception as e:
        logger.error("crawl_aborted", error=str(e))
        raise typer.Exit(code=1)


@app.command()
def stats():
    """Show database statistics."""
    settings = Settings.from_yaml()
    
    async def _stats():
        db = await get_db(settings.db_path)
        cur = await db.execute("SELECT COUNT(*) as c FROM crawled_urls")
        r = await cur.fetchone()
        print(f"Crawled URLs: {r['c']}")
        
        cur = await db.execute("SELECT COUNT(*) as c FROM exam_documents")
        r = await cur.fetchone()
        print(f"Stored Documents: {r['c']}")
        await db.close()
        
    asyncio.run(_stats())


@app.command()
def export(batch_name: str = typer.Option(None, help="Batch name")):
    """Export pending documents to batch_manifest.json for the Parser Agent."""
    settings = Settings.from_yaml()
    
    async def _export():
        db = await get_db(settings.db_path)
        cur = await db.execute("SELECT * FROM exam_documents WHERE parse_status = 'pending'")
        rows = await cur.fetchall()
        
        docs = [dict(r) for r in rows]
        
        if not docs:
            print("No pending documents to export.")
            await db.close()
            return
            
        manifest = {
            "batch_id": batch_name or f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "created_at": datetime.now().isoformat(),
            "total_files": len(docs),
            "files": docs
        }
        
        out_path = settings.data_path / "batch_manifest.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
            
        # Update status
        ids = [doc["id"] for doc in docs]
        placeholders = ",".join("?" * len(ids))
        await db.execute(f"UPDATE exam_documents SET parse_status = 'sent' WHERE id IN ({placeholders})", ids)
        await db.commit()
        await db.close()
        
        print(f"Exported {len(docs)} documents to {out_path}")
        
    asyncio.run(_export())


if __name__ == "__main__":
    app()
