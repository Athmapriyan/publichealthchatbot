"""
Central configuration. All secrets come from environment variables (.env).
Never hardcode API keys here.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # --- LLM provider chain (primary + fallbacks, tried in order) ---
    LLM_PROVIDER_ORDER = [
        p.strip() for p in os.getenv("LLM_PROVIDER_ORDER", "groq,gemini,openrouter").split(",") if p.strip()
    ]

    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free")

    HF_API_KEY = os.getenv("HF_API_KEY", "")

    # --- Sarvam AI (multilingual: translation + language identification) ---
    SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "")
    SARVAM_TRANSLATE_MODEL = os.getenv("SARVAM_TRANSLATE_MODEL", "sarvam-translate:v1")

    # --- RAG ---
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "./data/chroma_db")
    RAG_TOP_K = int(os.getenv("RAG_TOP_K", "4"))
    RAG_SCORE_THRESHOLD = float(os.getenv("RAG_SCORE_THRESHOLD", "0.35"))  # cosine similarity floor

    # --- Knowledge base ---
    KNOWLEDGE_BASE_PATH = os.getenv("KNOWLEDGE_BASE_PATH", "./knowledge_base/diseases.json")

    # --- App ---
    APP_ENV = os.getenv("APP_ENV", "development")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/app.db")

    # --- Supported languages (Phase 6 will expand this) ---
    SUPPORTED_LANGUAGES = [
    "en", "hi", "bn", "te", "mr", "ta", "gu", "ur", "kn", "or", "ml", "pa",
    "as", "mai", "sat", "ks", "ne", "sd", "doi", "kok", "mni", "brx", "sa",
]  # English + all 22 Scheduled Indian languages (via Sarvam AI) # English, Hindi, Odia


settings = Settings()
