from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from app.models.image_moderation_enums import MediaModerationStatus
from app.services.image_moderation_service import publish_block_reason_for_images

# Roots where system placeholder is allowed (no real photo required to go active).
PLACEHOLDER_ALLOWED_ROOTS: frozenset[str] = frozenset({
    "jobs",
    "services",
    "free-exchange",
    "ready-business",
})

# Physical / visual goods — at least one real (non-placeholder) photo to publish as active.
REAL_PHOTO_REQUIRED_ROOTS: frozenset[str] = frozenset({
    "transport",
    "real-estate",
    "electronics",
    "animals",
    "home-garden",
    "kids",
    "medical",
    "food-agri",
    "beauty",
    "fashion",
    "sports-hobby",
    "stationery-books",
    "materials",
    "business-equipment",
    "repair-construction",
})

_ALL_ROOTS: frozenset[str] = PLACEHOLDER_ALLOWED_ROOTS | REAL_PHOTO_REQUIRED_ROOTS

PHOTO_REMINDER_TEXT = (
    "Добавьте фотографии — объявления с фото получают больше просмотров "
    "и вызывают больше доверия."
)

PUBLISH_BLOCKED_NO_PHOTO = "Для публикации нужно добавить хотя бы одно фото."

PLACEHOLDER_MEDIA_URL = "/media/placeholders/listing-default.png"


@runtime_checkable
class ListingImageLike(Protocol):
    is_placeholder: bool


def category_root_slug(category_slug: str | None) -> str | None:
    if not category_slug:
        return None
    for root in sorted(_ALL_ROOTS, key=len, reverse=True):
        if category_slug == root or category_slug.startswith(f"{root}-"):
            return root
    return category_slug.split("-", 1)[0] if category_slug else None


def allows_placeholder_image(category_slug: str | None) -> bool:
    root = category_root_slug(category_slug)
    return root in PLACEHOLDER_ALLOWED_ROOTS if root else False


def requires_real_photo(category_slug: str | None) -> bool:
    if not category_slug:
        return True
    return not allows_placeholder_image(category_slug)


def is_placeholder_media(media: Any) -> bool:
    if getattr(media, "is_placeholder", False):
        return True
    url = getattr(media, "url", "") or ""
    return "/placeholders/" in url


def media_moderation_status_value(media: Any) -> str:
    status = getattr(media, "moderation_status", None)
    if status is None:
        return MediaModerationStatus.approved.value
    return status.value if hasattr(status, "value") else str(status)


def is_approved_for_publish(media: Any) -> bool:
    if is_placeholder_media(media):
        return True
    return media_moderation_status_value(media) == MediaModerationStatus.approved.value


def count_real_photos(images: list[Any] | None) -> int:
    if not images:
        return 0
    return sum(
        1
        for img in images
        if not is_placeholder_media(img) and is_approved_for_publish(img)
    )


def has_real_photo(images: list[Any] | None) -> bool:
    return count_real_photos(images) > 0


def validate_images_for_active_publish(images: list[Any] | None) -> str | None:
    return publish_block_reason_for_images(images)


def can_publish_active(
    *,
    category_slug: str | None,
    real_photo_count: int,
    uses_placeholder: bool = False,
    images: list[Any] | None = None,
) -> bool:
    if validate_images_for_active_publish(images):
        return False
    if real_photo_count > 0:
        return True
    if images is not None and count_real_photos(images) > 0:
        return True
    if allows_placeholder_image(category_slug):
        return uses_placeholder
    return False
