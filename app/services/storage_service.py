"""Image validation + ObjectStorage facade for media uploads.

Business code uses storage keys / public URLs — never filesystem paths.
"""

from __future__ import annotations

import logging
import re
import uuid

from fastapi import UploadFile

from app.core.config import Settings
from app.core.exceptions import AppException
from app.storage.base import ObjectStorage
from app.storage.factory import build_object_storage
from datetime import UTC, datetime, timedelta

from app.storage.capabilities import ObjectHead, PresignedUpload, PresigningStorage
from app.storage.keys import assert_safe_storage_key, opaque_upload_key
from app.storage.presigning import as_headable

logger = logging.getLogger(__name__)

_ALLOWED_CONTENT_TYPES = frozenset({"image/jpeg", "image/png", "image/webp"})
_CONTENT_TYPE_TO_EXT = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
MAX_IMAGE_UPLOAD_BYTES = 5 * 1024 * 1024
_LEGACY_FLAT_BASENAME = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.(jpg|png|webp)$",
    re.IGNORECASE,
)


def _magic_matches_head(content: bytes, content_type: str) -> bool:
    if content_type == "image/jpeg":
        return len(content) >= 3 and content[:3] == b"\xff\xd8\xff"
    if content_type == "image/png":
        return len(content) >= 8 and content.startswith(b"\x89PNG\r\n\x1a\n")
    if content_type == "image/webp":
        return len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"WEBP"
    return False


class StorageService:
    """Validates image payloads and delegates blob I/O to ObjectStorage."""

    def __init__(
        self,
        settings: Settings,
        backend: ObjectStorage | None = None,
    ) -> None:
        self._settings = settings
        self._backend: ObjectStorage = backend or build_object_storage(settings)
        base = settings.MEDIA_URL.strip() or "/media/"
        if not base.endswith("/"):
            base = f"{base}/"
        self._media_url_prefix = base

    @property
    def backend(self) -> ObjectStorage:
        return self._backend

    def validate_image(self, content: bytes, content_type: str) -> str:
        """Return normalized extension (.jpg/.png/.webp) or raise AppException."""
        if content_type not in _ALLOWED_CONTENT_TYPES:
            raise AppException(
                "Unsupported media type; allowed: image/jpeg, image/png, image/webp.",
                status_code=400,
            )
        if len(content) > MAX_IMAGE_UPLOAD_BYTES:
            raise AppException(
                "File too large; maximum size is 5 MB.",
                status_code=400,
            )
        if not _magic_matches_head(content, content_type):
            raise AppException(
                "File content does not match declared image type.",
                status_code=400,
            )
        return _CONTENT_TYPE_TO_EXT[content_type]

    @staticmethod
    def ext_from_content_type(content_type: str) -> str:
        if content_type not in _ALLOWED_CONTENT_TYPES:
            raise AppException(
                "Unsupported media type; allowed: image/jpeg, image/png, image/webp.",
                status_code=400,
            )
        return _CONTENT_TYPE_TO_EXT[content_type]

    @staticmethod
    def validate_declared_upload(content_type: str, content_length: int) -> None:
        if content_type not in _ALLOWED_CONTENT_TYPES:
            raise AppException(
                "Unsupported media type; allowed: image/jpeg, image/png, image/webp.",
                status_code=400,
            )
        if content_length <= 0 or content_length > MAX_IMAGE_UPLOAD_BYTES:
            raise AppException(
                "File too large; maximum size is 5 MB.",
                status_code=400,
            )

    def head_object(self, key: str) -> ObjectHead | None:
        return as_headable(self._backend).head_object(assert_safe_storage_key(key))

    def presign_put(
        self,
        key: str,
        *,
        listing_id: int,
        media_id: int,
        content_type: str,
        content_length: int,
    ) -> PresignedUpload:
        safe = assert_safe_storage_key(key)
        ttl = self._settings.MEDIA_PRESIGN_TTL_SECONDS
        backend = self._backend
        if isinstance(backend, PresigningStorage):
            return backend.presign_put(
                safe,
                content_type=content_type,
                content_length=content_length,
                expires_seconds=ttl,
            )
        expires_at = datetime.now(UTC) + timedelta(seconds=ttl)
        return PresignedUpload(
            method="PUT",
            url=f"/api/v1/listings/{listing_id}/media/{media_id}/upload",
            headers={"Content-Type": content_type},
            expires_at=expires_at,
        )

    def put_bytes(
        self,
        key: str,
        content: bytes,
        *,
        content_type: str | None = None,
    ) -> str:
        """Put bytes at server-side key; return public URL. Idempotent for same key."""
        safe = assert_safe_storage_key(key)
        self._backend.put(safe, content, content_type=content_type)
        return self._backend.public_url(safe)

    def public_url(self, key: str) -> str:
        return self._backend.public_url(assert_safe_storage_key(key))

    def exists_key(self, key: str) -> bool:
        return self._backend.exists(assert_safe_storage_key(key))

    def delete_key(self, key: str) -> None:
        """Idempotent delete by storage key."""
        self._backend.delete(assert_safe_storage_key(key))

    def save_image(self, content: bytes, content_type: str) -> str:
        """
        Opaque upload for chat/avatar (not listing key layout).
        Returns public URL; storage key is embedded in URL path for local backend.
        """
        ext = self.validate_image(content, content_type)
        key = opaque_upload_key(f"{uuid.uuid4()}{ext}")
        return self.put_bytes(key, content, content_type=content_type)

    def _legacy_key_from_url(self, stored_url: str) -> str | None:
        """Map legacy /media/{uuid}.ext or /media/{key...} URL to storage key."""
        raw = stored_url.strip()
        if not raw.startswith("/"):
            raw = f"/{raw.lstrip('/')}"
        prefix = self._media_url_prefix
        if not raw.startswith(prefix):
            return None
        rest = raw[len(prefix) :]
        if not rest or rest.startswith("/") or ".." in rest.split("/"):
            return None
        # Nested keys (new layout) or flat legacy uuid filename.
        try:
            return assert_safe_storage_key(rest)
        except AppException:
            return None

    def delete_file(self, stored_url: str) -> None:
        """
        Delete by public URL (legacy API used by chat/avatar/moderation).
        Idempotent when blob is already gone.
        """
        key = self._legacy_key_from_url(stored_url)
        if key is None:
            # Placeholders and foreign URLs are not deletable blobs.
            if "/placeholders/" in stored_url:
                return
            raise AppException("Invalid media URL.", status_code=400)
        # Extra guard for flat legacy basename pattern when single-segment.
        if "/" not in key and not _LEGACY_FLAT_BASENAME.match(key):
            # New opaque uploads/ under uploads/uuid.ext is multi-segment.
            raise AppException("Invalid media filename.", status_code=400)
        self._backend.delete(key)

    def stored_file_exists(self, stored_url: str) -> bool:
        key = self._legacy_key_from_url(stored_url)
        if key is None:
            raise AppException("Invalid media URL.", status_code=400)
        return self._backend.exists(key)

    def delete_media_blob(
        self,
        *,
        storage_key: str | None,
        public_url: str | None,
    ) -> None:
        """Prefer storage_key; fall back to public URL for legacy rows."""
        if storage_key:
            try:
                self.delete_key(storage_key)
                return
            except AppException:
                logger.warning("storage_delete_key_failed key=%s", storage_key)
                return
        if public_url:
            try:
                self.delete_file(public_url)
            except AppException:
                logger.warning("storage_delete_url_failed")


async def read_upload_limited(upload: UploadFile) -> tuple[bytes, str, str | None]:
    """Read body up to MAX_IMAGE_UPLOAD_BYTES; raises AppException if larger."""
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await upload.read(65536)
        if not chunk:
            break
        total += len(chunk)
        if total > MAX_IMAGE_UPLOAD_BYTES:
            raise AppException(
                "File too large; maximum size is 5 MB.",
                status_code=400,
            )
        chunks.append(chunk)
    raw_type = upload.content_type or ""
    source_name = upload.filename
    return (b"".join(chunks), raw_type.strip(), source_name)
