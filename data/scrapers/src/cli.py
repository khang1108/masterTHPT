from __future__ import annotations

import asyncio
import structlog
import typer

from exam_scraper.config import Settings
from exam_scraper.core import CrawlService
from exam_scraper.core import TOANMATH_DOMAIN
from exam_scraper.tool_api import CrawlToolInput, resolve_crawl_tool_input

logger = structlog.get_logger()
app = typer.Typer(help="ToanMath-only exam PDF scraper", no_args_is_help=True)


@app.callback()
def main() -> None:
    """ToanMath-only exam PDF scraper."""


@app.command()
def crawl(
    start_url: str = typer.Option(
        f"https://{TOANMATH_DOMAIN}",
        help="ToanMath URL to start crawling from",
    ),
    grade: str = typer.Option(None, help="Grade to filter"),
    subject: str = typer.Option(None, help="Subject to filter"),
    exam_type: str = typer.Option(None, "--exam-type", help="Exam type to filter"),
    query: str = typer.Option(None, "--query", help="Natural language query for subject/grade/exam type"),
    limit: int = typer.Option(10, help="Maximum PDFs to download"),
    force: bool = typer.Option(False, help="Bypass URL dedup cache"),
):
    """Crawl ToanMath and download exam PDFs."""
    settings = Settings.from_yaml()
    try:
        resolved = resolve_crawl_tool_input(
            CrawlToolInput(
                intent=query,
                start_url=start_url,
                subject=subject,
                grade=grade,
                exam_type=exam_type,
                limit=limit,
                force=force,
            ),
            settings=settings,
        )
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc

    if force:
        cleared = asyncio.run(CrawlService(settings).clear_cache())
        logger.info("cache_cleared", domain=TOANMATH_DOMAIN, rows=cleared)

    service = CrawlService(settings)
    for note in resolved.notes:
        logger.warning("resolved_filter_note", note=note)

    async def _run_crawl():
        downloaded = await service.run(
            start_url=resolved.start_url,
            limit=resolved.limit,
            allowed_subjects=resolved.allowed_subjects,
            grade_filter=resolved.grade,
            exam_type_filter=resolved.exam_type,
        )
        typer.echo(f"Downloaded {downloaded} PDF(s) from {TOANMATH_DOMAIN}.")

    try:
        asyncio.run(_run_crawl())
    except Exception as e:
        logger.error("crawl_aborted", error=str(e))
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
