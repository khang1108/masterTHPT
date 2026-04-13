import re

def group_blocks_into_questions(parsing_blocks: list, page_visual_crops: dict) -> list[dict]:
    """
    Gom nhóm dữ liệu thô (Grouping Script).
    Dựa vào tọa độ (bbox) để map hình ảnh vào đúng câu hỏi.
    
    Args:
        parsing_blocks: Danh sách các khối layout (vd: text, figure, formula) trả về từ OCR.
        page_visual_crops: Dictionary chứa mapping {fig_id: base64_image_data} trả về từ OCR.
        
    Returns:
        Một danh sách các rổ câu hỏi (Question chunks). 
        Mỗi rổ là một Dictionary:
        {
            "raw_text": str,
            "images": { "fig_id": "base64..." },
            "bbox": [x1, y1, x2, y2],
            "min_y": float,
            "max_y": float
        }
    """
    # Bước 1: Phân rã khối text/formula và khối ảnh (figure)
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
    
    # Bước 2: Gom các khối text vào rổ tương ứng bằng Regex "Câu N"
    for block in text_blocks:
        content = block.get('content', '').strip()
        # [x1, y1, x2, y2]
        bbox = block.get('bbox', [0, 0, 0, 0])
        label = block.get('label', 'text')
        
        # Regex tìm từ khóa bắt đầu câu hỏi (Ví dụ: "Câu 12:", "Câu 1.", "Bài 1 ")
        match = re.search(r'(?i)(câu|bài)\s*\d+[\.:\s]', content)
        
        # Nếu block này chứa "Câu XX" ở ngay đầu (index < 15)
        if match and match.start() < 15:
            if current_q:
                questions.append(current_q)
            current_q = {
                "raw_text": f"[{label}] {content}",
                "bbox": list(bbox), # clone bbox 
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
            
            # Móc nối text
            if current_q["raw_text"]:
                current_q["raw_text"] += f"\n[{label}] {content}"
            else:
                current_q["raw_text"] = f"[{label}] {content}"
                
            # Mở rộng bounding box toàn cục của câu hỏi này
            current_q["bbox"][0] = min(current_q["bbox"][0], bbox[0])
            current_q["bbox"][1] = min(current_q["bbox"][1], bbox[1])
            current_q["bbox"][2] = max(current_q["bbox"][2], bbox[2])
            current_q["bbox"][3] = max(current_q["bbox"][3], bbox[3])
            
            current_q["min_y"] = min(current_q["min_y"], bbox[1])
            current_q["max_y"] = max(current_q["max_y"], bbox[3])
            
    # Push chunk cuối cùng vào mảng
    if current_q:
        questions.append(current_q)
        
    # Bước 3: Map ảnh vào đúng câu hỏi dựa vào Tọa độ dọc (Y-coordinate)
    for fig in figure_blocks:
        fig_bbox = fig.get('bbox', [0, 0, 0, 0])
        # Lấy Y-center của hình để map 
        fig_y_center = (fig_bbox[1] + fig_bbox[3]) / 2.0
        
        fig_id = str(fig.get('block_id', ''))
        img_path = None
        
        # Mapping path từ ID
        for key, path_info in page_visual_crops.items():
            if key.endswith(f"_{fig_id}") or key == fig_id:
                img_path = path_info
                break
                
        if not img_path:
            continue
            
        # Tìm câu hỏi phù hợp nhất
        best_q = None
        for q in questions:
            # Câu hỏi chứa ảnh thường có tọa độ Y trên đỉnh (min_y) nhỏ hơn tâm ảnh (fig_y_center)
            if fig_y_center >= q["min_y"]:
                best_q = q
            else:
                # Do các câu hỏi xếp theo min_y từ trên xuống dưới, ta có thể dừng
                break
                
        if best_q:
            # Lưu abs_path để Gemini có thể mở file ảo, và web_url để nhúng vào prompt JSON
            best_q["image_urls"].append(img_path["abs_path"])
            best_q["raw_text"] += f"\\n[FIGURE_URL: {img_path['web_url']}]"
            
    return questions
