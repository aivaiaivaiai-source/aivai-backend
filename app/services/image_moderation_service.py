from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.models.image_moderation_enums import ImageModerationVerdict, MediaModerationStatus
from app.schemas.image_moderation import ImageClassificationInput, ImageModerationOutcome
from app.services.image_policy_classifier import ImagePolicyClassifier, StubImagePolicyClassifier

IMAGE_REJECTED_USER_MESSAGE = (
    "Похоже, фото нарушает правила платформы AiVai. "
    "Пожалуйста, загрузите другое изображение."
)

IMAGE_MODERATION_QUEUE_USER_MESSAGE = "Фото отправлено на проверку модератору."

PUBLISH_BLOCKED_REJECTED_MEDIA = (
    "Нельзя опубликовать объявление: одно или несколько фото отклонены модерацией."
)

PUBLISH_BLOCKED_QUEUE_MEDIA = (
    "Нельзя опубликовать объявление: фото ожидают проверки модератором."
)

PUBLISH_BLOCKED_PENDING_MEDIA = (
    "Нельзя опубликовать объявление: фото ещё проходят проверку."
)


def verdict_to_status(verdict: ImageModerationVerdict) -> MediaModerationStatus:
    if verdict == ImageModerationVerdict.ALLOW:
        return MediaModerationStatus.approved
    if verdict == ImageModerationVerdict.REJECT:
        return MediaModerationStatus.rejected
    return MediaModerationStatus.moderation_queue


def build_moderation_reason(result_reason_code: str | None, result_detail: str | None) -> str | None:
    if not result_reason_code and not result_detail:
        return None
    if result_reason_code and result_detail:
        return f"{result_reason_code}: {result_detail}"
    return result_reason_code or result_detail


def media_status_value(media: Any) -> str:
    status = getattr(media, "moderation_status", None)
    if status is None:
        return MediaModerationStatus.approved.value
    return status.value if hasattr(status, "value") else str(status)


def publish_block_reason_for_images(images: list[Any] | None) -> str | None:
    if not images:
        return None
    for img in images:
        if getattr(img, "is_placeholder", False):
            continue
        url = getattr(img, "url", "") or ""
        if "/placeholders/" in url:
            continue
        status = media_status_value(img)
        if status == MediaModerationStatus.rejected.value:
            return PUBLISH_BLOCKED_REJECTED_MEDIA
        if status == MediaModerationStatus.moderation_queue.value:
            return PUBLISH_BLOCKED_QUEUE_MEDIA
        if status == MediaModerationStatus.pending.value:
            return PUBLISH_BLOCKED_PENDING_MEDIA
    return None


def assistant_message_for_images(images: list[Any] | None) -> str | None:
    if not images:
        return None
    has_rejected = False
    has_queue = False
    for img in images:
        if getattr(img, "is_placeholder", False):
            continue
        status = media_status_value(img)
        if status == MediaModerationStatus.rejected.value:
            has_rejected = True
        elif status == MediaModerationStatus.moderation_queue.value:
            has_queue = True
    if has_rejected:
        return IMAGE_REJECTED_USER_MESSAGE
    if has_queue:
        return IMAGE_MODERATION_QUEUE_USER_MESSAGE
    return None


class ImageModerationService:
    def __init__(self, classifier: ImagePolicyClassifier | None = None) -> None:
        self._classifier = classifier or StubImagePolicyClassifier()

    async def run_classification(
        self,
        payload: ImageClassificationInput,
    ) -> ImageModerationOutcome:
        result = await self._classifier.classify(payload)
        status = verdict_to_status(result.verdict)
        return ImageModerationOutcome(
            media_id=0,
            verdict=result.verdict,
            moderation_status=status,
            moderation_reason=build_moderation_reason(
                result.reason_code,
                result.reason_detail,
            ),
            moderated_at=datetime.now(UTC),
            blocked_from_listing=result.verdict == ImageModerationVerdict.REJECT,
        )
