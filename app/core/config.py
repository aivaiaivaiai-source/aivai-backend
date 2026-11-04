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
    # local = LocalDiskStorage + StaticFiles; s3 = S3CompatibleStorage (R2/MinIO/AWS).
    MEDIA_STORAGE_BACKEND: str = "local"
    MEDIA_S3_ENDPOINT_URL: str | None = None
    MEDIA_S3_BUCKET: str | None = None
    MEDIA_S3_REGION: str | None = None
    MEDIA_S3_ACCESS_KEY: str | None = None
    MEDIA_S3_SECRET_KEY: str | None = None
    MEDIA_S3_PUBLIC_BASE_URL: str | None = None
    MEDIA_S3_ADDRESSING_STYLE: str = "path"

    OPENAI_API_KEY: str | None = None

    TTS_AUDIO_TTL_HOURS: int = 24

    # Inactive assistant chats (by last_activity_at); auto-cleaned while API runs.
    ASSISTANT_CONVERSATION_TTL_DAYS: int = 7
    ASSISTANT_CONVERSATION_CLEANUP_ENABLED: bool = True
    ASSISTANT_CONVERSATION_CLEANUP_INTERVAL_HOURS: float = 24
    ASSISTANT_CONVERSATION_CLEANUP_BATCH_SIZE: int = 2000
    ASSISTANT_CONVERSATION_CLEANUP_MAX_BATCHES: int = 500
    ASSISTANT_CONVERSATION_CLEANUP_BATCH_PAUSE_MS: int = 50

    CATEGORY_SNAPSHOT_TTL_SECONDS: int = 60

    # Currency V2: header key for PUT /fx/usd-kgs (empty disables mutation).
    FX_RATE_ADMIN_KEY: str = "aivai-fx-dev"

    FOCUS_BBOX_ENABLED: bool = True
    FOCUS_BBOX_MODEL_ID: str = "PekingU/rtdetr_r18vd_coco_o365"
    FOCUS_BBOX_MIN_CONFIDENCE: float = 0.35

    # Paid AI search assistants: expire subscriptions + drain match queue.
    AI_AGENT_MAINTENANCE_INTERVAL_SECONDS: float = 300

    # Redis for AI match queue + realtime pub/sub. Empty → in-memory fallback.
    REDIS_URL: str = "redis://127.0.0.1:6379/0"

    # Optional read replica for AI history (falls back to primary).
    POSTGRES_READ_SERVER: str | None = None

    # --- Media Platform async pipeline (Stage 3) — default OFF ---
    MEDIA_ASYNC_PIPELINE_ENABLED: bool = False
    MEDIA_ASYNC_PIPELINE_VERSION: str = "v2"
    MEDIA_QUEUE_NAMESPACE: str = "aivai:media"
    MEDIA_JOB_LEASE_SECONDS: int = 300
    MEDIA_JOB_MAX_ATTEMPTS: int = 5
    MEDIA_JOB_RETRY_BACKOFF_SECONDS: str = "15,60,300,900,3600"
    MEDIA_JOB_PROCESSING_TIMEOUT_SECONDS: int = 120
    MEDIA_OUTBOX_DISPATCH_BATCH: int = 50
    MEDIA_JOB_RECONCILE_BATCH: int = 100
    MEDIA_WORKER_BLOCK_MS: int = 5000
    MEDIA_WORKER_CONSUMER_NAME: str = ""
    MEDIA_WORKER_MIN_REPLICAS: int = 1
    MEDIA_WORKER_MAX_REPLICAS: int = 10
    MEDIA_QUEUE_MAX_BACKLOG: int = 100_000

    # --- Media Engine (Stage 4) ---
    MEDIA_PIPELINE_VERSION: str = "v2"
    MEDIA_MAX_DECODE_PIXELS: int = 20_000_000
    MEDIA_MAX_IMAGE_BYTES: int = 5 * 1024 * 1024
    MEDIA_DETECTOR_TIMEOUT_SECONDS: int = 30
    MEDIA_DETECTOR_INFERENCE_MAX_EDGE: int = 1280
    MEDIA_ENGINE_JPEG_QUALITY: int = 88
    MEDIA_ENGINE_DISPLAY_LONG_EDGE: int = 1600
    MEDIA_ENGINE_FEED_LONG_EDGE: int = 800
    MEDIA_ENGINE_THUMB_LONG_EDGE: int = 320

    # --- Media AI Classification (Stage 6C Substage 2) — default OFF ---
    MEDIA_AI_CLASSIFICATION_ENABLED: bool = False
    MEDIA_CLASSIFIER_VERSION: str = "dev-deterministic-v1"
    MEDIA_CLASSIFICATION_MAX_IMAGES: int = 3
    MEDIA_CLASSIFICATION_INFERENCE_MAX_EDGE: int = 640
    MEDIA_CLASSIFICATION_HIGH_CONFIDENCE: float = 0.85
    MEDIA_CLASSIFICATION_MEDIUM_CONFIDENCE: float = 0.55
    MEDIA_CLASSIFICATION_TIMEOUT_SECONDS: int = 60

    # --- User intent for hybrid classification (Substage 3C-1) — default OFF ---
    MEDIA_USER_INTENT_ENABLED: bool = False

    # --- Category Resolver shadow mode (Substage 3C-3) — default OFF ---
    CATEGORY_RESOLVER_ENABLED: bool = False
    CATEGORY_RESOLVER_AUTO_ASSIGN_ENABLED: bool = False
    # --- Draft category enrichment from resolver (Substage 3C-4) — default OFF ---
    CATEGORY_RESOLVER_DRAFT_ENRICHMENT_ENABLED: bool = False

    # --- Local visual evidence (Substage 3C-2) — default OFF ---
    MEDIA_VISUAL_EVIDENCE_ENABLED: bool = False
    MEDIA_VISUAL_EVIDENCE_MAX_IMAGES: int = 3
    MEDIA_VISUAL_EVIDENCE_TIMEOUT_SECONDS: int = 120
    MEDIA_VISUAL_EVIDENCE_USE_STUB: bool = False

    # --- Description mode UX (Substage 3C-2) — default OFF ---
    MEDIA_DESCRIPTION_MODE_ENABLED: bool = False

    # --- Direct upload + CDN (Stage 5) — default OFF ---
    MEDIA_DIRECT_UPLOAD_ENABLED: bool = False
    MEDIA_CDN_BASE_URL: str | None = None
    MEDIA_ORIGINAL_PUBLIC: bool = False
    MEDIA_PRESIGN_TTL_SECONDS: int = 900
    MEDIA_UPLOAD_RESERVATION_TTL_SECONDS: int = 3600
    MEDIA_MAX_INCOMPLETE_UPLOADS_PER_USER: int = 20
    MEDIA_DIRECT_UPLOAD_INITIATE_PER_MINUTE: int = 30
    MEDIA_STORAGE_CLEANUP_BATCH: int = 50
    MEDIA_STORAGE_CLEANUP_MAX_ATTEMPTS: int = 5
    MEDIA_UPLOAD_CLEANUP_BATCH: int = 100

    def media_job_retry_backoff_list(self) -> list[int]:
        raw = (self.MEDIA_JOB_RETRY_BACKOFF_SECONDS or "").strip()
        if not raw:
            return [60]
        out: list[int] = []
        for part in raw.split(","):
            part = part.strip()
            if not part:
                continue
            try:
                out.append(max(1, int(part)))
            except ValueError:
                continue
        return out or [60]

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

    @computed_field
    @property
    def DATABASE_READ_URL(self) -> str:
        host = (self.POSTGRES_READ_SERVER or self.POSTGRES_SERVER).strip()
        user = quote_plus(self.POSTGRES_USER)
        password = quote_plus(self.POSTGRES_PASSWORD)
        return (
            f"{ASYNC_DATABASE_DRIVER}://{user}:{password}"
            f"@{host}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
