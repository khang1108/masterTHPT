from __future__ import annotations

import re
from bs4 import BeautifulSoup

from exam_scraper.utils.url_utils import (
    is_pdf_url,
    resolve_url,
    extract_gdrive_id,
    gdrive_direct_url,
)


class PdfExtractor:
    _DOWNLOAD_KEYWORDS = re.compile(
        r"(tải|download|tải về|tải xuống|tải file|xem đề|pdf|\.pdf)",
        re.IGNORECASE,
    )

    def extract_from_html(self, html: str, base_url: str) -> list[str]:
        soup = BeautifulSoup(html, "html.parser")
        urls: list[str] = []
        seen: set[str] = set()

        for tag in soup.find_all("a", href=True):
            href = tag["href"].strip()
            full_url = resolve_url(base_url, href)
            if full_url in seen:
                continue
            seen.add(full_url)

            if is_pdf_url(full_url):
                urls.append(full_url)
                continue

            gid = extract_gdrive_id(full_url)
            if gid:
                direct = gdrive_direct_url(gid)
                if direct not in seen:
                    urls.append(direct)
                    seen.add(direct)
                continue

            text = tag.get_text(strip=True)
            if self._DOWNLOAD_KEYWORDS.search(text) or self._DOWNLOAD_KEYWORDS.search(href):
                if any(ext in href.lower() for ext in [".pdf", "download", "file"]):
                    urls.append(full_url)

        for tag in soup.find_all("iframe", src=True):
            src = tag["src"].strip()
            full_url = resolve_url(base_url, src)
            gid = extract_gdrive_id(full_url)
            if gid:
                direct = gdrive_direct_url(gid)
                if direct not in seen:
                    urls.append(direct)
                    seen.add(direct)
            elif is_pdf_url(full_url) and full_url not in seen:
                urls.append(full_url)
                seen.add(full_url)

        for tag in soup.find_all("embed", src=True):
            src = tag["src"].strip()
            full_url = resolve_url(base_url, src)
            if is_pdf_url(full_url) and full_url not in seen:
                urls.append(full_url)
                seen.add(full_url)

        return urls

    def extract_listing_links(self, html: str, base_url: str, pattern: str = "") -> list[str]:
        soup = BeautifulSoup(html, "html.parser")
        urls: list[str] = []
        seen: set[str] = set()
        regex = re.compile(pattern) if pattern else None

        for tag in soup.find_all("a", href=True):
            href = tag["href"].strip()
            full_url = resolve_url(base_url, href)
            if full_url in seen:
                continue
            seen.add(full_url)
            if regex and regex.search(full_url):
                urls.append(full_url)
            elif not regex:
                urls.append(full_url)

        return urls
