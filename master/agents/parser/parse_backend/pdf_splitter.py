import os
import fitz


def split_pdf_to_images(pdf_path: str, output_dir: str | None = None, dpi: int = 300) -> list[str]:
    """Tách từng trang PDF thành ảnh PNG (300 DPI) cho OCR."""
    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"Không tìm thấy file PDF: {pdf_path}")

    if output_dir is None:
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        output_dir = os.path.join(os.path.dirname(pdf_path), f"{base_name}_pages")

    os.makedirs(output_dir, exist_ok=True)

    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)

    doc = fitz.open(pdf_path)
    image_paths: list[str] = []

    print(f"[PDF Splitter] Đang tách {doc.page_count} trang từ: {os.path.basename(pdf_path)}")

    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)
        pix = page.get_pixmap(matrix=matrix, alpha=False)

        filename = f"page_{page_num + 1:03d}.png"
        filepath = os.path.join(output_dir, filename)

        pix.save(filepath)
        image_paths.append(os.path.abspath(filepath))
        print(f"Trang {page_num + 1}/{doc.page_count} → {filename} ({pix.width}x{pix.height}px)")

    doc.close()
    print(f"{len(image_paths)} ảnh đã lưu tại: {output_dir}")

    return image_paths
