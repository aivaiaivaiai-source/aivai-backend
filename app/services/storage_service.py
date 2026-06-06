from __future__ import annotations

import re
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.config import Settings
from app.core.exceptions import AppException

_ALLOWED_CONTENT_TYPES = frozenset({"image/jpeg", "image/png", "image/webp"})
_CONTENT_TYPE_TO_EXT = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
MAX_IMAGE_UPLOAD_BYTES = 5 * 1024 * 1024
_SAFE_STORED_BASENAME = re.compile(
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
    """Filesystem access for media files. No database or authorization here."""

    def __init__(self, settings: Settings) -> None:
        self._root = Path(settings.MEDIA_ROOT).resolve()
        self._media_url = settings.MEDIA_URL

    def _public_url(self, filename: str) -> str:
        base = self._media_url
        if not base.endswith("/"):
            base = f"{base}/"
        return f"{base}{filename}"

    def _validate_payload(self, content: bytes, content_type: str) -> str:
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

    def save_image(self, content: bytes, content_type: str) -> str:
        ext = self._validate_payload(content, content_type)
        filename = f"{uuid.uuid4()}{ext}"
        path = self._root / filename
        self._root.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return self._public_url(filename)

    def _resolve_stored_path(self, stored_url: str) -> Path:
        expected_prefix = self._media_url
        if not expected_prefix.endswith("/"):
            expected_prefix = f"{expected_prefix}/"
        raw = stored_url.strip()
        if not raw.startswith("/"):
            raw = f"/{raw.lstrip('/')}"
        if not raw.startswith(expected_prefix):
            raise AppException("Invalid media URL.", status_code=400)
        basename = raw[len(expected_prefix) :]
        if not basename or "/" in basename or basename in (".", ".."):
            raise AppException("Invalid media path.", status_code=400)
        if not _SAFE_STORED_BASENAME.match(basename):
            raise AppException("Invalid media filename.", status_code=400)
        resolved = (self._root / basename).resolve()
        try:
            resolved.relative_to(self._root)
        except ValueError as exc:
            raise AppException("Invalid media path.", status_code=400) from exc
        return resolved

    def stored_file_exists(self, stored_url: str) -> bool:
        """True if the resolved file exists; False if missing. Invalid URL/path raises AppException."""
        path = self._resolve_stored_path(stored_url)
        return path.is_file()

    def delete_file(self, stored_url: str) -> None:
        resolved = self._resolve_stored_path(stored_url)
        if resolved.is_file():
            resolved.unlink()


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
