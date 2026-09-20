from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Monarch API"
    app_env: str = "development"
    database_url: str = "postgresql+asyncpg://monarch:monarch@127.0.0.1:5432/monarch"
    cors_origins: list[str] = ["http://127.0.0.1:3000", "http://localhost:3000"]
    upload_dir: Path = Path(".data/quote_uploads")
    quote_draft_retention_hours: int = 24
    quote_accepted_retention_days: int = 30
    quote_unhandled_retention_days: int = 90
    quote_cleanup_interval_seconds: int = 60
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    admin_base_url: str = ""
    admin_allowed_emails: list[str] = []
    cloudflare_access_team_domain: str = ""
    cloudflare_access_aud: str = ""
    admin_dev_token: str = ""

    @property
    def telegram_enabled(self) -> bool:
        return bool(self.telegram_bot_token and self.telegram_chat_id)

    @property
    def cloudflare_access_issuer(self) -> str:
        domain = self.cloudflare_access_team_domain.strip().rstrip("/")
        if not domain:
            return ""
        if not domain.startswith("https://"):
            domain = f"https://{domain}"
        return domain

    @property
    def normalized_admin_emails(self) -> set[str]:
        return {email.strip().casefold() for email in self.admin_allowed_emails if email.strip()}

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
