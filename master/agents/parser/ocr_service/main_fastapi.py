import base64
import io
import os
import cv2
import numpy as np
from fastapi import FastAPI, UploadFile, File, HTTPException
import uvicorn
from pyngrok import ngrok
from kaggle_secrets import UserSecretsClient
from PIL import Image

# Khởi tạo các Modules
from preprocessing_textbook import preprocess_image
from layout_parser import LayoutParser

user_secrets = UserSecretsClient()
secret_value_1 = user_secrets.get_secret("NGROK_AUTH_TOKEN")

os.environ["MODELSCOPE_DOMAIN"] = "modelscope.cn"
os.environ["MS_REGION"] = "cn"

app = FastAPI(title="Kaggle OCR Microservice")

# Khởi tạo model (Synchronous)
print("[*] Bắt đầu tải Model PP-StructureV3. Vui lòng chờ...")
try:
    layout_parser = LayoutParser()
    print("[*] Tuyệt vời! Model đã được tải hoàn tất 100%!")
except Exception as e:
    print("[!] FATAL ERROR TO DOWNLOAD/LOAD MODELS:")
    import traceback
    traceback.print_exc()
    raise e


def pil_to_base64(img_pil: Image.Image) -> str:
    """Chuyển PIL Image thành base64 string."""
    buf = io.BytesIO()
    img_pil.save(buf, format='JPEG')
    return base64.b64encode(buf.getvalue()).decode('utf-8')


def nparray_to_base64(img_np: np.ndarray) -> str:
    """Mã hóa ảnh numpy thành base64."""
    _, buffer = cv2.imencode('.jpg', img_np)
    return base64.b64encode(buffer).decode('utf-8')


@app.post("/extract_ocr")
async def extract_ocr(image: UploadFile = File(...)):
    """
    Nhận ảnh → PP-StructureV3 xử lý trọn gói → trả latex + markdown + figures.
    
    PP-StructureV3 tự động thực hiện:
        1. Layout Detection (phát hiện vùng text/formula/figure/table)
        2. Text OCR (PP-OCRv5)
        3. Formula Recognition (PP-FormulaNet)
        4. Table Recognition
    
    Trả về:
        - latex_content: Nội dung đầy đủ kèm LaTeX formulas
        - markdown_content: Nội dung markdown  
        - visual_base64_crops: Ảnh figure/table đã crop (base64)
        - block_count: Số blocks layout đã phát hiện
    """
    try:
        contents = await image.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            raise HTTPException(status_code=400, detail="Invalid image file")

        print(f"[*] Image received: {img.shape}, preprocessing...")
        processed_img = preprocess_image(img)

        print("[*] Running PP-StructureV3 (Layout + OCR + Formula)...")
        extraction = layout_parser.extract(processed_img)

        # Chuyển figure images (PIL) thành base64 để gửi qua JSON
        visual_base64_crops = {}
        for fig_id, fig_img in extraction.get("figure_images", {}).items():
            try:
                if isinstance(fig_img, Image.Image):
                    visual_base64_crops[fig_id] = pil_to_base64(fig_img)
            except Exception as e:
                print(f"  [!] Error encoding figure {fig_id}: {e}")

        latex_content = extraction.get("latex_content", "")
        markdown_content = extraction.get("markdown_content", "")
        block_count = len(extraction.get("parsing_blocks", []))

        print(f"[*] Done! latex={len(latex_content)} chars, md={len(markdown_content)} chars, "
              f"figures={len(visual_base64_crops)}, blocks={block_count}")

        return {
            "status": "success",
            "latex_content": latex_content,
            "markdown_content": markdown_content,
            "combined_raw_text": latex_content,  # backward compatibility
            "visual_base64_crops": visual_base64_crops,
            "block_count": block_count,
            "layout_count": block_count,  # backward compatibility
            "parsing_blocks": extraction.get("parsing_blocks", [])
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/debug_preprocess")
async def debug_preprocess(image: UploadFile = File(...)):
    """DEBUG ENDPOINT — Kiểm tra preprocessing + raw PP-StructureV3 output."""
    try:
        contents = await image.read()
        nparr = np.frombuffer(contents, np.uint8)
        img_original = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img_original is None:
            raise HTTPException(status_code=400, detail="Invalid image file")

        processed_img = preprocess_image(img_original)
        original_b64 = nparray_to_base64(img_original)
        processed_b64 = nparray_to_base64(processed_img)

        # Chạy extraction
        extraction = layout_parser.extract(processed_img)

        return {
            "original_shape": list(img_original.shape),
            "processed_shape": list(processed_img.shape),
            "original_image_base64": original_b64,
            "processed_image_base64": processed_b64,
            "latex_content": extraction.get("latex_content", ""),
            "markdown_content": extraction.get("markdown_content", ""),
            "block_count": len(extraction.get("parsing_blocks", [])),
            "parsing_blocks_sample": extraction.get("parsing_blocks", [])[:5],
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":

    ngrok.set_auth_token(secret_value_1)
    try:
        ngrok.kill()
    except Exception:
        pass
    # Ép buộc Ngrok chỉ bind vào IPv4 để tránh lỗi dial tcp [::1]:8000 connection refused
    public_url = ngrok.connect("127.0.0.1:8000")
    print("=" * 50)
    print(f"🚀 Kaggle Public URL: {public_url}")
    print("🔔 HÃY COPY ĐƯỜNG DẪN TRÊN VÀ BỎ VÀO .env (KAGGLE_NGROK_URL)!")
    print("=" * 50)

    uvicorn.run(app, host="127.0.0.1", port=8000)
