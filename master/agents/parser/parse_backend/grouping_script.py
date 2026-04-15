import re


def group_blocks_into_questions(parsing_blocks: list, page_visual_crops: dict) -> list[dict]:
    """Gom nhóm blocks OCR thành các câu hỏi, map hình ảnh theo tọa độ Y."""
    text_blocks = []
    figure_blocks = []

    for block in parsing_blocks:
        label = block.get('label', '')
        if label in ('figure', 'figure_image', 'image'):
            figure_blocks.append(block)
        else:
            text_blocks.append(block)

    questions = []
    current_q = None

    # Gom text blocks theo regex "Câu N"
    for block in text_blocks:
        content = block.get('content', '').strip()
        bbox = block.get('bbox', [0, 0, 0, 0])
        label = block.get('label', 'text')

        match = re.search(r'(?i)(câu|bài)\s*\d+[\.:\s]', content)

        if match and match.start() < 15:
            if current_q:
                questions.append(current_q)
            current_q = {
                "raw_text": f"[{label}] {content}",
                "bbox": list(bbox),
                "min_y": bbox[1],
                "max_y": bbox[3],
                "image_urls": []
            }
        else:
            if not current_q:
                current_q = {
                    "raw_text": "",
                    "bbox": list(bbox),
                    "min_y": bbox[1],
                    "max_y": bbox[3],
                    "image_urls": []
                }

            if current_q["raw_text"]:
                current_q["raw_text"] += f"\n[{label}] {content}"
            else:
                current_q["raw_text"] = f"[{label}] {content}"

            current_q["bbox"][0] = min(current_q["bbox"][0], bbox[0])
            current_q["bbox"][1] = min(current_q["bbox"][1], bbox[1])
            current_q["bbox"][2] = max(current_q["bbox"][2], bbox[2])
            current_q["bbox"][3] = max(current_q["bbox"][3], bbox[3])

            current_q["min_y"] = min(current_q["min_y"], bbox[1])
            current_q["max_y"] = max(current_q["max_y"], bbox[3])

    if current_q:
        questions.append(current_q)

    # Map ảnh vào câu hỏi dựa theo Y-coordinate
    for fig in figure_blocks:
        fig_bbox = fig.get('bbox', [0, 0, 0, 0])
        fig_y_center = (fig_bbox[1] + fig_bbox[3]) / 2.0

        fig_id = str(fig.get('block_id', ''))
        img_path = None

        for key, path_info in page_visual_crops.items():
            if key.endswith(f"_{fig_id}") or key == fig_id:
                img_path = path_info
                break

        if not img_path:
            continue

        best_q = None
        for q in questions:
            if fig_y_center >= q["min_y"]:
                best_q = q
            else:
                break

        if best_q:
            best_q["image_urls"].append(img_path["abs_path"])
            best_q["raw_text"] += f"\\n[FIGURE_URL: {img_path['web_url']}]"

    return questions
