import argparse
import os
import re
import shutil
import unicodedata

import fitz


def _normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text or "")
    normalized = "".join(
        char for char in normalized if unicodedata.category(char) != "Mn"
    )
    normalized = normalized.replace("đ", "d").replace("Đ", "D")
    return normalized.lower()


def _contains_marker(text: str, markers: tuple[str, ...]) -> bool:
    normalized = _normalize_text(text)
    compact = re.sub(r"[^a-z0-9]+", "", normalized)

    for marker in markers:
        if re.search(rf"\b{re.escape(marker)}\b", normalized):
            return True
        if marker in compact:
            return True

    return False


def _page_has_start_marker(page) -> bool:
    return _contains_marker(page.get_text("text"), ("so", "de"))


def _page_has_end_marker(page) -> bool:
    text = _normalize_text(page.get_text("text"))
    marker_chars = r"\-–—_.=~*•·"
    return re.search(
        rf"(?<![a-z0-9])[{marker_chars}]+\s*het\s*[{marker_chars}]+(?![a-z0-9])",
        text,
    ) is not None


def _find_split_range(document) -> tuple[int, int] | None:
    start_page_index = None

    for page_index in range(document.page_count):
        page = document.load_page(page_index)

        if start_page_index is None and _page_has_start_marker(page):
            start_page_index = page_index

        if start_page_index is not None and _page_has_end_marker(page):
            return start_page_index, page_index

    if start_page_index is not None:
        return start_page_index, document.page_count - 1

    return None


def _split_range_is_too_large(start_page_index: int, end_page_index: int) -> bool:
    return end_page_index - start_page_index + 1 >= 5


def _render_pdf_pages_to_images(document, image_dir: str, dpi: int) -> list[str]:
    if os.path.isdir(image_dir):
        shutil.rmtree(image_dir)

    os.makedirs(image_dir, exist_ok=True)
    zoom = dpi / 72
    matrix = fitz.Matrix(zoom, zoom)
    image_paths: list[str] = []

    for page_index in range(document.page_count):
        image_path = os.path.join(image_dir, f"{page_index + 1}.png")
        pixmap = document.load_page(page_index).get_pixmap(matrix=matrix, alpha=False)
        pixmap.save(image_path)
        image_paths.append(os.path.abspath(image_path))

    return image_paths


def split_pdf_to_pdf(
    pdf_path: str,
    output_dir: str | None = None,
    image_dpi: int = 300,
) -> str | None:
    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(pdf_path), "output")

    os.makedirs(output_dir, exist_ok=True)

    document = fitz.open(pdf_path)
    output_document = fitz.open()
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    output_path = os.path.abspath(
        os.path.join(output_dir, f"{base_name}_split.pdf")
    )
    image_dir = os.path.abspath(os.path.join(output_dir, base_name))

    print(f"[PDF] Scan {document.page_count} pages from {os.path.basename(pdf_path)}")

    split_range = _find_split_range(document)
    if split_range is None:
        document.close()
        output_document.close()
        print("[PDF] Complete marker range not found")
        return None

    start_page_index, end_page_index = split_range
    if _split_range_is_too_large(start_page_index, end_page_index):
        page_count = end_page_index - start_page_index + 1
        document.close()
        output_document.close()
        print(f"[PDF] Split range too large ({page_count} pages)")
        return None

    print(f"[PDF] Start at page {start_page_index + 1}")
    print(f"[PDF] Stop at page {end_page_index + 1}")

    output_document.insert_pdf(
        document,
        from_page=start_page_index,
        to_page=end_page_index,
    )
    output_document.save(output_path)
    image_paths = _render_pdf_pages_to_images(output_document, image_dir, image_dpi)

    output_document.close()
    document.close()

    print(f"[PDF] Saved {output_path}")
    print(f"[PDF] Saved {len(image_paths)} images")
    return output_path


def split_pdf_to_images(
    pdf_path: str,
    output_dir: str | None = None,
    dpi: int = 300,
) -> list[str]:
    output_path = split_pdf_to_pdf(pdf_path, output_dir=output_dir, image_dpi=dpi)
    if not output_path:
        return []

    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    image_dir = os.path.join(os.path.dirname(output_path), base_name)
    return [
        os.path.abspath(os.path.join(image_dir, file_name))
        for file_name in sorted(
            os.listdir(image_dir),
            key=lambda name: int(name.split(".")[0]),
        )
        if file_name.endswith(".png")
    ]


def split_many_pdfs(pdf_paths: list[str], output_dir: str | None = None) -> int:
    failed = 0

    for pdf_path in pdf_paths:
        try:
            result = split_pdf_to_pdf(pdf_path, output_dir=output_dir)
        except Exception as error:
            failed += 1
            print(f"[PDF] Failed {pdf_path}: {error}")
            continue

        if not result:
            failed += 1

    return failed


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Split PDF exams and render numbered page images."
    )
    parser.add_argument("pdf_paths", nargs="+", help="PDF file paths to split.")
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Optional shared output directory. Defaults to <pdf_dir>/output.",
    )
    args = parser.parse_args()

    return split_many_pdfs(args.pdf_paths, output_dir=args.output_dir)


if __name__ == "__main__":
    raise SystemExit(main())
