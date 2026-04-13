"""
PDF Splitter Module
-------------------
Tách từng trang PDF thành ảnh PNG riêng biệt (300 DPI) để tối ưu cho OCR.
Output được tổ chức vào cây thư mục chuẩn:

    output_dir/
    ├── page_001.png
    ├── page_002.png
    └── ...
"""

import os
import fitz  # PyMuPDF


def split_pdf_to_images(
    pdf_path: str,
    output_dir: str | None = None,
    dpi: int = 300
) -> list[str]:
    """
    Mở file PDF, render mỗi trang thành 1 ảnh PNG với độ phân giải `dpi`.
    
    Args:
        pdf_path:   Đường dẫn tuyệt đối tới file PDF.
        output_dir: Thư mục lưu ảnh. Nếu None → tạo thư mục cùng tên PDF cạnh file gốc.
        dpi:        Dots per inch cho rendering (default 300 để OCR chính xác).
        
    Returns:
        List đường dẫn tuyệt đối tới các file PNG đã tạo, theo thứ tự trang.
    """
    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"Không tìm thấy file PDF: {pdf_path}")
    
    # Xây dựng cây thư mục output
    if output_dir is None:
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        output_dir = os.path.join(os.path.dirname(pdf_path), f"{base_name}_pages")
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Tính zoom factor từ DPI (PyMuPDF default = 72 DPI)
    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)
    
    doc = fitz.open(pdf_path)
    image_paths: list[str] = []
    
    print(f"[PDF Splitter] Đang tách {doc.page_count} trang từ: {os.path.basename(pdf_path)}")
    
    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)
        
        # Render trang thành pixmap (ảnh bitmap)
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        
        # Đặt tên file theo thứ tự: page_001.png, page_002.png, ...
        filename = f"page_{page_num + 1:03d}.png"
        filepath = os.path.join(output_dir, filename)
        
        pix.save(filepath)
        image_paths.append(os.path.abspath(filepath))
        
        print(f"    ✓ Trang {page_num + 1}/{doc.page_count} → {filename} ({pix.width}x{pix.height}px)")
    
    doc.close()
    print(f"[PDF Splitter] Hoàn tất! {len(image_paths)} ảnh đã lưu tại: {output_dir}")
    
    return image_paths
