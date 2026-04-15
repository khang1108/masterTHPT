import asyncio
from exam_scraper.config import Settings
from exam_scraper.core.http_client import HttpClient

async def main():
    settings = Settings()
    http = HttpClient(settings)
    html = await http.fetch_with_cloudscraper("https://toanmath.com")
    print(f"HTML Length: {len(html)}")
    print(html[:500])

asyncio.run(main())
