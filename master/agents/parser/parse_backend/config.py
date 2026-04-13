import os
from dotenv import load_dotenv

load_dotenv()

class ParserConfig:
    # GEMINI
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = "gemini-2.5-flash"
    
    # OCR
    USE_GPU = True
    LANG = "vi" # default paddleocr language for Vietnamese
    
    # Preprocessing
    BINARIZE_THRESHOLD = 128
    
    # Allowed formats
    ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}

    # ===== KAGGLE ENDPOINT CONNECTIVITY =====
    # Cấu hình địa chỉ Public Ngrok URL của Kaggle OCR Service
    KAGGLE_NGROK_URL = os.getenv("KAGGLE_NGROK_URL", "https://ammonia-slate-country.ngrok-free.dev")
    # ===== MONGODB ENDPOINT CONNECTIVITY =====
    MONGO_URI = os.getenv("MONGO_URI", "")
    MONGO_DB = os.getenv("MONGO_DB", "")
    MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "")

config = ParserConfig()
