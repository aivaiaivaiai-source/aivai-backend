"""Server-side storage key layout. Never accept client paths as keys."""

from __future__ import annotations

import re

from app.core.exceptions import AppException

_VARIANT_NAMES = frozenset({"original", "display", "feed", "thumb"})
_SAFE_EXT = frozenset({".jpg", ".jpeg", ".png", ".webp"})
_KEY_SEGMENT = re.compile(r"^[A-Za-z0-9._-]+$")
_PIPELINE_VERSION = re.compile(r"^[a-zA-Z0-9._-]{1,32}$")


def normalize_ext(ext: str) -> str:
    e = ext.lower().strip()
    if not e.startswith("."):
        e = f".{e}"
    if e == ".jpeg":
        e = ".jpg"
    if e not in _SAFE_EXT:
        raise AppException("Unsupported media extension.", status_code=400)
    return e


def assert_safe_storage_key(key: str) -> str:
    """Reject traversal, absolute paths, and empty/unsafe segments."""
    raw = (key or "").strip().replace("\\", "/")
    if not raw:
        raise AppException("Invalid storage key.", status_code=400)
    if raw.startswith("/") or raw.startswith("~") or ":" in raw:
        raise AppException("Invalid storage key.", status_code=400)
    if ".." in raw.split("/"):
        raise AppException("Invalid storage key.", status_code=400)
    parts = [p for p in raw.split("/") if p != ""]
    if not parts or any(p in (".", "..") for p in parts):
        raise AppException("Invalid storage key.", status_code=400)
    for part in parts:
        if not _KEY_SEGMENT.match(part):
            raise AppException("Invalid storage key.", status_code=400)
    return "/".join(parts)


def listing_media_variant_key(
    listing_id: int,
    media_id: int,
    variant: str,
    ext: str,
    *,
    pipeline_version: str | None = None,
) -> str:
    """
    Canonical listing media key, e.g.:
      media/{listing_id}/{media_id}/original.jpg
      media/{listing_id}/{media_id}/v1/display.jpg  (versioned variants)
    """
    if listing_id <= 0 or media_id <= 0:
        raise AppException("Invalid listing/media id for storage key.", status_code=400)
    if variant not in _VARIANT_NAMES:
        raise AppException("Invalid media variant name.", status_code=400)
    safe_ext = normalize_ext(ext)
    version_segment = ""
    if pipeline_version is not None:
        ver = pipeline_version.strip()
        if not ver or not _PIPELINE_VERSION.match(ver):
            raise AppException("Invalid pipeline version for storage key.", status_code=400)
        version_segment = f"{ver}/"
    return assert_safe_storage_key(
        f"media/{listing_id}/{media_id}/{version_segment}{variant}{safe_ext}",
    )


def listing_original_key(listing_id: int, media_id: int, ext: str) -> str:
    return listing_media_variant_key(listing_id, media_id, "original", ext)


def opaque_upload_key(filename: str) -> str:
    """Flat unique key for chat/avatar uploads (not listing media layout)."""
    return assert_safe_storage_key(f"uploads/{filename}")
