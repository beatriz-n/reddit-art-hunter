from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Reddit Art Hunter API"
    app_env: str = "development"
    log_level: str = "INFO"
    database_url: str | None = None
    cors_allow_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    data_dir: Path = Path(__file__).resolve().parents[3] / "data"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str | None = None
    ollama_embedding_model: str | None = None
    ollama_timeout_seconds: float = 180.0
    reddit_access_token: str | None = None
    reddit_user_agent: str = "RedditArtHunter/0.1 (local personal app)"
    reddit_api_approved: bool = False

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allow_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
