"""CDN/public URL resolution from storage keys (Stage 5)."""

from __future__ import annotations

from app.core.config import Settings
from app.models.media import Media
from app.models.media_enums import MediaLifecycleStatus
from app.schemas.media import MediaVariantsRead
from app.storage.keys import assert_safe_storage_key


class MediaDeliveryService:
    """
    Resolve storage keys → client-facing URLs.
    DB may store keys; CDN base is configurable without DB rewrite.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        media_url = (settings.MEDIA_URL or "/media/").strip()
        if not media_url.endswith("/"):
            media_url = f"{media_url}/"
        self._local_base = media_url
        cdn = (settings.MEDIA_CDN_BASE_URL or "").strip()
        if cdn and not cdn.endswith("/"):
            cdn = f"{cdn}/"
        self._cdn_base = cdn or None

    def _variant_base(self) -> str:
        return self._cdn_base or self._local_base

    def public_variant_url(self, storage_key: str | None) -> str | None:
        if not storage_key:
            return None
        if not self._is_public_deliverable_key(storage_key):
            return None
        safe = assert_safe_storage_key(storage_key)
        return f"{self._variant_base()}{safe}"

    def original_url(self, storage_key: str | None, *, fallback: str | None = None) -> str | None:
        """Original is private in production; only expose when explicitly allowed."""
        if not storage_key:
            return fallback
        if self._settings.MEDIA_ORIGINAL_PUBLIC:
            safe = assert_safe_storage_key(storage_key)
            return f"{self._variant_base()}{safe}"
        return fallback

    def resolve_variants(self, media: Media) -> MediaVariantsRead:
        legacy = media.url
        original_key = getattr(media, "original_storage_key", None)
        original = self.original_url(
            original_key,
            fallback=getattr(media, "original_url", None) or legacy,
        )
        display_key = getattr(media, "display_storage_key", None)
        feed_key = getattr(media, "feed_storage_key", None)
        thumb_key = getattr(media, "thumb_storage_key", None)

        display = (
            self.public_variant_url(display_key)
            if display_key and self._lifecycle_allows_public_variants(media)
            else getattr(media, "display_url", None) or legacy
        )
        feed = (
            self.public_variant_url(feed_key)
            if feed_key and self._lifecycle_allows_public_variants(media)
            else getattr(media, "feed_url", None)
        )
        thumb = (
            self.public_variant_url(thumb_key)
            if thumb_key and self._lifecycle_allows_public_variants(media)
            else getattr(media, "thumb_url", None)
        )
        return MediaVariantsRead(
            original=original,
            display=display,
            feed=feed,
            thumb=thumb,
        )

    @staticmethod
    def _lifecycle_allows_public_variants(media: Media) -> bool:
        status = media.lifecycle_status
        return status in (
            MediaLifecycleStatus.ready,
            MediaLifecycleStatus.processing,
        )

    @staticmethod
    def _is_public_deliverable_key(key: str) -> bool:
        lower = key.lower()
        if "/original." in lower:
            return False
        return any(part in lower for part in ("/display.", "/feed.", "/thumb."))
