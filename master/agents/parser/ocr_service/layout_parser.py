"""
Layout Parser — Wrapper cho PP-StructureV3
--------------------------------------------
Trích xuất trực tiếp latex, markdown, và parsing_res_list từ PP-StructureV3.

Tham khảo API chính thức:
https://github.com/PaddlePaddle/PaddleOCR/blob/main/docs/version3.x/pipeline_usage/PP-StructureV3.md

LayoutParsingResultV2 là dict-like object, có các thuộc tính:
    - res['latex']       → dict với 'latex_blocks': [{type, content}, ...]
    - res['markdown']    → dict với 'markdown_texts': [str, ...]
    - res['json']        → dict với 'res': {parsing_res_list: [{block_bbox, block_label, block_content, ...}]}
    
QUAN TRỌNG: 
    - block_bbox là np.ndarray (KHÔNG phải list), cần .tolist()
    - Khi truy cập res['json'], object trả về CÓ THỂ là dict hoặc property
    - Dùng save_to_json() để dump ra file nếu cần debug
"""

import sys
import json
import unittest.mock
from importlib.machinery import ModuleSpec

# --- KAGGLE NCCL FATAL CRASH FIX ---
dummy_torch = unittest.mock.MagicMock()
dummy_torch.__spec__ = ModuleSpec(name="torch", loader=None)
dummy_torch.__version__ = "2.6.0"
dummy_torch.__path__ = []

sys.modules['torch'] = dummy_torch
sys.modules['torchvision'] = dummy_torch
sys.modules['torch.multiprocessing'] = dummy_torch
sys.modules['torch.distributed'] = dummy_torch
sys.modules['torch.utils'] = dummy_torch

from paddleocr import PPStructureV3
import numpy as np


class LayoutParser:
    def __init__(self):
        self.pipeline = PPStructureV3()

    def extract(self, image: np.ndarray) -> dict:
        """
        Chạy PP-StructureV3 toàn bộ pipeline.
        
        Returns:
            {
                "latex_content": str,
                "markdown_content": str,
                "parsing_blocks": list[dict],
                "figure_images": dict,
            }
        """
        output = self.pipeline.predict(image, format_block_content=True)
        
        result = {
            "latex_content": "",
            "markdown_content": "",
            "parsing_blocks": [],
            "figure_images": {},
        }
        
        for res in output:
            # Debug: in ra kiểu và keys thực tế
            print(f"  [LayoutParser] Result type: {type(res).__name__}")
            
            # --- STRATEGY 1: Dùng save_to_json rồi đọc lại (đáng tin cậy nhất) ---
            try:
                import tempfile, os
                tmp_json = os.path.join(tempfile.gettempdir(), "_ppstructure_debug.json")
                res.save_to_json(tmp_json)
                with open(tmp_json, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                os.remove(tmp_json)
                
                # json_data là dict với key 'res'
                inner = json_data if 'parsing_res_list' in json_data else json_data.get('res', json_data)
                
                blocks = inner.get('parsing_res_list', [])
                for block in blocks:
                    bbox = block.get('block_bbox', [0, 0, 0, 0])
                    # Có thể là list hoặc nested list
                    if isinstance(bbox, list) and len(bbox) > 0 and isinstance(bbox[0], list):
                        # Flatten polygon [[x1,y1],[x2,y2],...] → [x1,y1,x2,y2]
                        bbox = [bbox[0][0], bbox[0][1], bbox[2][0], bbox[2][1]]
                    
                    result["parsing_blocks"].append({
                        "label": block.get('block_label', 'unknown'),
                        "bbox": bbox,
                        "content": block.get('block_content', ''),
                        "block_id": block.get('block_id', -1),
                    })
                
                print(f"  [LayoutParser] Extracted {len(result['parsing_blocks'])} blocks from JSON")
            except Exception as e:
                print(f"  [LayoutParser] JSON extraction fallback: {e}")

            # --- LATEX (cho Gemini structuring) ---
            try:
                latex_data = getattr(res, 'latex', None)
                if isinstance(latex_data, dict):
                    blocks = latex_data.get('latex_blocks', [])
                    parts = []
                    for block in blocks:
                        if isinstance(block, dict):
                            content = block.get('content', '')
                            block_type = block.get('type', 'text')
                            parts.append(f"[{block_type}] {content}")
                    result["latex_content"] = "\n".join(parts)
                elif isinstance(latex_data, str):
                    result["latex_content"] = latex_data
                    
                print(f"  [LayoutParser] LaTeX: {len(result['latex_content'])} chars")
            except Exception as e:
                print(f"  [LayoutParser] LaTeX extraction error: {e}")
            
            # --- MARKDOWN ---
            try:
                md_data = getattr(res, 'markdown', None)
                if isinstance(md_data, dict):
                    md_texts = md_data.get('markdown_texts', [])
                    if isinstance(md_texts, list):
                        result["markdown_content"] = "\n".join(str(t) for t in md_texts)
                    
                    # Lấy ảnh inline
                    md_images = md_data.get('markdown_images', {})
                    if isinstance(md_images, dict):
                        result["figure_images"] = md_images
                elif isinstance(md_data, str):
                    result["markdown_content"] = md_data
                    
                print(f"  [LayoutParser] Markdown: {len(result['markdown_content'])} chars, "
                      f"figures: {len(result['figure_images'])}")
            except Exception as e:
                print(f"  [LayoutParser] Markdown extraction error: {e}")
        
        return result
