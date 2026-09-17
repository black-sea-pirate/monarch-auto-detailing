from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Monarch API"
    app_env: str = "development"
    database_url: str = "postgresql+asyncpg://monarch:monarch@127.0.0.1:5432/monarch"
    cors_origins: list[str] = ["http://127.0.0.1:3000", "http://localhost:3000"]
    upload_dir: Path = Path(".data/quote_uploads")
    quote_retention_hours: int = 168
    quote_cleanup_interval_seconds: int = 3600
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    telegram_webhook_url: str = ""
    telegram_webhook_secret: str = ""

    @property
    def telegram_enabled(self) -> bool:
        return bool(self.telegram_bot_token and self.telegram_chat_id)

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
