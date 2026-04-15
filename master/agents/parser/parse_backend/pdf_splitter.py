import os
import unicodedata

import fitz


def _normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text or "")
    normalized = "".join(
        char for char in normalized if unicodedata.category(char) != "Mn"
    )
    normalized = normalized.replace("đ", "d").replace("Đ", "D")
    return normalized.lower()


def _page_contains_text(page, needle: str) -> bool:
    return needle in _normalize_text(page.get_text("text"))


def split_pdf_to_images(
    pdf_path: str,
    output_dir: str | None = None,
    dpi: int = 300,
) -> list[str]:
    """Save pages from the first SO page to the last HET page."""
    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    if output_dir is None:
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        output_dir = os.path.join(os.path.dirname(pdf_path), f"{base_name}_pages")

    os.makedirs(output_dir, exist_ok=True)

    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)
    document = fitz.open(pdf_path)
    image_paths: list[str] = []

    start_page_index = None
    end_page_index = None

    print(f"[PDF] Split {document.page_count} pages from {os.path.basename(pdf_path)}")

    for page_index in range(document.page_count):
        page = document.load_page(page_index)
        has_so = _page_contains_text(page, "so")
        has_het = _page_contains_text(page, "het")

        if start_page_index is None and has_so:
            start_page_index = page_index

        if has_het:
            end_page_index = page_index

    if start_page_index is None:
        document.close()
        print("[PDF] Start marker not found")
        return []

    if end_page_index is None or end_page_index < start_page_index:
        end_page_index = document.page_count - 1

    print(f"[PDF] Start at page {start_page_index + 1}")
    print(f"[PDF] Stop at page {end_page_index + 1}")

    for page_index in range(start_page_index, end_page_index + 1):
        page = document.load_page(page_index)

        pixmap = page.get_pixmap(matrix=matrix, alpha=False)
        filename = f"page_{page_index + 1:03d}.png"
        filepath = os.path.join(output_dir, filename)

        pixmap.save(filepath)
        image_paths.append(os.path.abspath(filepath))
        print(f"[PDF] Saved {filename}")

    document.close()
    print(f"[PDF] Saved {len(image_paths)} page images")
    return image_paths
