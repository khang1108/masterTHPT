import os
from dotenv import load_dotenv

load_dotenv()

class ParserConfig:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = "gemini-2.5-flash"

    USE_GPU = True
    LANG = "vi"
    BINARIZE_THRESHOLD = 128
    ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}

    KAGGLE_NGROK_URL = os.getenv("KAGGLE_NGROK_URL", "https://ammonia-slate-country.ngrok-free.dev")

    MONGO_URI = os.getenv("MONGO_URI", "")
    MONGO_DB = os.getenv("MONGO_DB", "")
    MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "")

config = ParserConfig()
