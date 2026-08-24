"""Build ObjectStorage from settings (DI — no branching in MediaService)."""

from __future__ import annotations

from app.core.config import Settings
from app.core.exceptions import AppException
from app.storage.base import ObjectStorage
from app.storage.local import LocalDiskStorage
from app.storage.s3 import S3CompatibleStorage


def build_object_storage(settings: Settings) -> ObjectStorage:
    backend = (settings.MEDIA_STORAGE_BACKEND or "local").strip().lower()
    if backend == "local":
        return LocalDiskStorage(
            settings.MEDIA_ROOT,
            public_base_url=settings.MEDIA_URL,
        )
    if backend == "s3":
        return S3CompatibleStorage(
            bucket=settings.MEDIA_S3_BUCKET or "",
            endpoint_url=settings.MEDIA_S3_ENDPOINT_URL,
            region=settings.MEDIA_S3_REGION,
            access_key=settings.MEDIA_S3_ACCESS_KEY,
            secret_key=settings.MEDIA_S3_SECRET_KEY,
            public_base_url=settings.MEDIA_S3_PUBLIC_BASE_URL or "",
            addressing_style=settings.MEDIA_S3_ADDRESSING_STYLE or "path",
        )
    raise AppException(
        f"Unsupported MEDIA_STORAGE_BACKEND={backend!r}; use local|s3.",
        status_code=503,
    )


def should_mount_static_media(settings: Settings) -> bool:
    """StaticFiles is only valid for LocalDiskStorage."""
    return (settings.MEDIA_STORAGE_BACKEND or "local").strip().lower() == "local"
