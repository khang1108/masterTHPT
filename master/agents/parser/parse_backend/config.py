import os

from dotenv import load_dotenv


ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=ENV_PATH)


class ParserConfig:
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip().strip('"').strip("'")
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.1"))

    USE_GPU = True
    LANG = "vi"
    BINARIZE_THRESHOLD = 128
    ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}

    KAGGLE_NGROK_URL = os.getenv(
        "KAGGLE_NGROK_URL",
        "https://ammonia-slate-country.ngrok-free.dev",
    ).strip()

    MONGO_URI = os.getenv("MONGO_URI", "").strip()
    MONGO_DB = os.getenv("MONGO_DB", "").strip()
    MONGO_COLLECTION_EXAMS = os.getenv("MONGO_COLLECTION_EXAMS", "exams").strip()
    MONGO_COLLECTION_QUESTIONS = os.getenv(
        "MONGO_COLLECTION_QUESTIONS",
        os.getenv("MONGO_COLLECTION", "questions"),
    ).strip()


config = ParserConfig()
