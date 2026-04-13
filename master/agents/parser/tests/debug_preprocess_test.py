"""
Debug Preprocessing — Gọi /debug_preprocess trên Kaggle
---------------------------------------------------------
Gửi 1 ảnh trang lên endpoint debug, lưu lại:
  - Ảnh gốc (original)
  - Ảnh sau preprocessing
  - Raw PP-StructureV3 output (JSON dump đầy đủ)
  - Parsed layout elements

Cách dùng:
    python debug_preprocess_test.py                          # Dùng page_001.png từ step1
    python debug_preprocess_test.py path/to/image.png        # Chỉ định ảnh cụ thể
"""

import os
import sys
import json
import base64
import requests

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from config import config

DEBUG_DIR = os.path.join(current_dir, "debug_output", "preprocess_check")
os.makedirs(DEBUG_DIR, exist_ok=True)


def test_debug_preprocess(image_path: str):
    api_url = f"{config.KAGGLE_NGROK_URL.rstrip('/')}/debug_preprocess"

    print(f"🔬 DEBUG PREPROCESSING")
    print(f"  📤 Ảnh: {image_path}")
    print(f"  🌐 URL: {api_url}")

    with open(image_path, "rb") as f:
        files = {"image": (os.path.basename(image_path), f, "image/png")}
        response = requests.post(api_url, files=files, timeout=120)
        response.raise_for_status()

    data = response.json()

    # === 1. Lưu ảnh gốc vs preprocessed ===
    for key, filename in [("original_image_base64", "1_original.jpg"),
                          ("processed_image_base64", "2_preprocessed.jpg")]:
        if key in data:
            img_bytes = base64.b64decode(data[key])
            path = os.path.join(DEBUG_DIR, filename)
            with open(path, "wb") as f:
                f.write(img_bytes)
            print(f"  💾 {filename}: {len(img_bytes)//1024} KB")

    # Raw ppstructure không truy xuất được nên ta lược qua
    pass

    # === 3. Lưu parsed elements ===
    parsed = data.get("parsing_blocks_sample", [])
    parsed_file = os.path.join(DEBUG_DIR, "4_parsed_elements.json")
    with open(parsed_file, "w", encoding="utf-8") as f:
        json.dump(parsed, f, ensure_ascii=False, indent=2)
    print(f"  💾 4_parsed_elements.json")

    # === 4. Lưu LaTeX content ===
    latex_content = data.get("latex_content", "")
    latex_file = os.path.join(DEBUG_DIR, "5_latex_content.txt")
    with open(latex_file, "w", encoding="utf-8") as f:
        f.write(latex_content)
    print(f"  💾 5_latex_content.txt")

    # === 5. Lưu Markdown content ===
    md_content = data.get("markdown_content", "")
    md_file = os.path.join(DEBUG_DIR, "6_markdown_content.md")
    with open(md_file, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"  💾 6_markdown_content.md")

    # === 6. In tóm tắt ===
    print(f"\n📊 KẾT QUẢ:")
    print(f"  Original shape:    {data.get('original_shape')}")
    print(f"  Processed shape:   {data.get('processed_shape')}")
    print(f"  Total blocks:      {data.get('block_count')}")
    print(f"  LaTeX length:      {len(latex_content)} chars")
    print(f"  Markdown length:   {len(md_content)} chars")

    print(f"\n🔍 PARSED LAYOUT ELEMENTS (Mẫu 5 block đầu):")
    for elem in parsed:
        print(f"  label='{elem.get('label')}', content_len={len(elem.get('content', ''))}, bbox={elem.get('bbox')}")

    print(f"\n📁 Tất cả output: {DEBUG_DIR}")
    print(f"   Mở ảnh 1_original.jpg và 2_preprocessed.jpg để so sánh!")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        img_path = sys.argv[1]
    else:
        # Tự tìm page_001.png từ step1
        default = os.path.join(current_dir, "debug_output", "step1_pages", "page_001.png")
        if os.path.exists(default):
            img_path = default
        else:
            print("❌ Cần chỉ định ảnh! Ví dụ: python debug_preprocess_test.py page.png")
            sys.exit(1)

    test_debug_preprocess(img_path)
