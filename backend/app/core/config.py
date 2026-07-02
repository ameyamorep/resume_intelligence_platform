from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Resume Intelligence Platform"

    # AI provider: "auto" picks the first configured of anthropic > gemini > groq > ollama.
    # Set explicitly to "anthropic" | "gemini" | "groq" | "ollama" | "none".
    ai_provider: str = "auto"

    anthropic_api_key: str = ""
    claude_model: str = "claude-fable-5"
    claude_fallback_model: str = "claude-opus-4-8"

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"
    database_url: str = "sqlite:///./resume_intel.db"
    embedding_model: str = "sentence-transformers/all-mpnet-base-v2"
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
