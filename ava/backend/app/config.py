import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _env(name: str, default=""):
    def _get():
        return os.getenv(name, default)

    return field(default_factory=_get)


def _env_bool(name: str, default: bool = False):
    def _get():
        value = os.getenv(name)
        if value is None or str(value).strip() == "":
            return default
        return str(value).strip().lower() in {"1", "true", "yes", "on"}

    return field(default_factory=_get)


def _env_int(name: str, default: int):
    def _get():
        try:
            return int(os.getenv(name)) if os.getenv(name) is not None else default
        except (TypeError, ValueError):
            return default

    return field(default_factory=_get)


def _env_float(name: str, default: float):
    def _get():
        try:
            return float(os.getenv(name)) if os.getenv(name) is not None else default
        except (TypeError, ValueError):
            return default

    return field(default_factory=_get)


def _env_list(name: str):
    def _get():
        return [o.strip() for o in os.getenv(name, "").split(",") if o.strip()]

    return field(default_factory=_get)


@dataclass(frozen=True)
class Settings:
    # LLM / Groq
    groq_api_key: str = _env("GROQ_API_KEY")
    llm_provider: str = _env("LLM_PROVIDER", "ollama")
    llm_model: str = _env("LLM_MODEL", "mixtral-8x7b-32768")
    llm_temperature: float = _env_float("LLM_TEMPERATURE", 0.3)
    llm_max_tokens: int = _env_int("LLM_MAX_TOKENS", 512)

    # Local model via Ollama
    ollama_base_url: str = _env("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model: str = _env("OLLAMA_MODEL", "qwen2.5-coder:1.5b")

    # Retrieval
    embedding_model: str = _env("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    vector_store_dir: str = _env("VECTOR_STORE_DIR", str(BASE_DIR / "data" / "vector_store"))
    retriever_k: int = _env_int("RETRIEVER_K", 4)
    retriever_min_score: float = _env_float("RETRIEVER_MIN_SCORE", 0.35)
    csv_data_file: str = _env("CSV_DATA_FILE", str(BASE_DIR / "data" / "combined_mental_health_dataset.csv"))

    # Conversation memory
    max_conversations: int = _env_int("MAX_CONVERSATIONS", 30)
    max_input_chars: int = _env_int("MAX_INPUT_CHARS", 2000)

    # Storage
    database_path: str = _env("DATABASE_PATH", str(BASE_DIR / "data" / "manobal.db"))

    # CORS
    cors_origins: list = _env_list("CORS_ORIGINS")

    # Clerk auth
    auth_enabled: bool = _env_bool("AUTH_ENABLED", True)
    clerk_issuer: str = _env("CLERK_ISSUER")
    clerk_audience: str = _env("CLERK_AUDIENCE", "manobal-frontend")
    clerk_jwks_url: str = _env("CLERK_JWKS_URL")

    # Emotion analysis
    emotion_model: str = _env("EMOTION_MODEL", "j-hartmann/emotion-english-distilroberta-base")
    emotion_device: str = _env("EMOTION_DEVICE", "cpu")

    # Quotes
    quotes_file: str = _env("QUOTES_FILE", str(BASE_DIR / "data" / "mental_health_quotes.txt"))

    @property
    def auth_required(self) -> bool:
        return self.auth_enabled and bool(self.clerk_jwks_url)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()