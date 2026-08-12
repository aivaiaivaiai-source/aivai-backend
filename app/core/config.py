from functools import lru_cache
from pathlib import Path
from urllib.parse import quote_plus

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

ASYNC_DATABASE_DRIVER = "postgresql+asyncpg"

# Resolve .env from project root so uvicorn/docker cwd does not break loading.
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_ENV_FILE = _PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILE if _ENV_FILE.is_file() else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    POSTGRES_USER: str = "aivai"
    POSTGRES_PASSWORD: str = "aivai_secret"
    POSTGRES_DB: str = "aivai"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432

    JWT_SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    MEDIA_ROOT: str = "media"
    MEDIA_URL: str = "/media/"

    OPENAI_API_KEY: str | None = None

    TTS_AUDIO_TTL_HOURS: int = 24

    CATEGORY_SNAPSHOT_TTL_SECONDS: int = 60

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        # Строго asyncpg; user/password кодируются для безопасных URL.
        # Пример: postgresql+asyncpg://user:password@db:5432/dbname
        user = quote_plus(self.POSTGRES_USER)
        password = quote_plus(self.POSTGRES_PASSWORD)
        return (
            f"{ASYNC_DATABASE_DRIVER}://{user}:{password}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
