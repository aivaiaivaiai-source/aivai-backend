from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Any

from app.models.enums import Currency, ListingStatus
from app.schemas.listing import ListingCreate
from app.schemas.listing_assistant import DraftPreview, PromotionOffer
from app.schemas.user import UserRead
from app.schemas.voice import VoiceCommandResponse, VoiceIntent
from app.services.listing_content_generator import ListingContentGenerator
from app.services.listing_service import ListingService
from app.services.image_moderation_service import (
    IMAGE_MODERATION_QUEUE_USER_MESSAGE,
    IMAGE_REJECTED_USER_MESSAGE,
    assistant_message_for_images,
)
from app.services.photo_requirement_policy import (
    PHOTO_REMINDER_TEXT,
    PUBLISH_BLOCKED_NO_PHOTO,
    allows_placeholder_image,
    count_real_photos,
    requires_real_photo,
)
from app.services.promotion_flow import PromotionFlow
from app.services.voice_response_builder import VoiceResponseBuilder
from app.services.voice_session_store import VoiceDialogueSession

_CONFIRM_PUBLISH = re.compile(
    r"(?:подтверждаю|опубликовать|публикую|да,? публикуй|готово,? публикуй|yes,? publish)",
    re.IGNORECASE,
)
_PHOTO_ACK = re.compile(
    r"(?:добавлю фото|добавить фото|загружу фото|позже фото|без фото|пропустить фото)",
    re.IGNORECASE,
)


class ListingCreationAssistant:
    PREVIEW_MESSAGE = (
        "Я подготовил черновик объявления. Проверьте данные и подтвердите публикацию."
    )
    PUBLISH_PROMPT = "Напишите «подтверждаю» или «опубликовать», когда будете готовы."

    def __init__(self, listing_service: ListingService) -> None:
        self._listings = listing_service
        self._responses = VoiceResponseBuilder
        self._content = ListingContentGenerator
        self._promotion = PromotionFlow

    def enrich_known_with_generated(
        self,
        session: VoiceDialogueSession,
        known: dict[str, Any],
    ) -> tuple[str, str]:
        title = session.generated_title or self._content.generate_title(
            seed_text=session.seed_text,
            known_fields=known,
            category_slug=session.category_slug,
        )
        description = session.generated_description or self._content.generate_description(
            title=title,
            known_fields=known,
            category_slug=session.category_slug,
            category_name=session.category_name,
            seed_text=session.seed_text,
        )
        session.generated_title = title
        session.generated_description = description
        known = dict(known)
        known["title"] = title
        known["description"] = description
        return title, description

    def build_draft_preview(
        self,
        *,
        category_id: int,
        category_slug: str | None,
        category_name: str | None,
        known_fields: dict[str, Any],
        title: str,
        description: str,
    ) -> DraftPreview:
        return DraftPreview(
            title=title,
            description=description,
            category_id=category_id,
            category_slug=category_slug,
            category_name=category_name,
            known_fields=dict(known_fields),
            price=_str_field(known_fields.get("price")),
            currency=_str_field(known_fields.get("currency")) or Currency.KGS.value,
            city=_str_field(known_fields.get("city")),
            real_photo_required=requires_real_photo(category_slug),
            placeholder_allowed=allows_placeholder_image(category_slug),
        )

    def ready_for_preview(
        self,
        intent: VoiceIntent,
        session: VoiceDialogueSession,
        known: dict[str, Any],
    ) -> VoiceCommandResponse:
        title, description = self.enrich_known_with_generated(session, known)
        session.known_fields = dict(known)
        session.flow_stage = "publish_preview"
        session.photos_reminder_shown = True

        preview = self.build_draft_preview(
            category_id=int(session.category_id or 0),
            category_slug=session.category_slug,
            category_name=session.category_name,
            known_fields=known,
            title=title,
            description=description,
        )
        message = f"{self.PREVIEW_MESSAGE} {PHOTO_REMINDER_TEXT} {self.PUBLISH_PROMPT}"
        needs_photos = requires_real_photo(session.category_slug)
        return self._responses.draft_preview(
            intent,
            preview=preview,
            message=message,
            needs_photos=needs_photos,
            real_photo_required=needs_photos,
        )

    @staticmethod
    def is_publish_confirmation(text: str) -> bool:
        return bool(_CONFIRM_PUBLISH.search(text.strip()))

    async def publish_confirmed(
        self,
        intent: VoiceIntent,
        session: VoiceDialogueSession,
        current_user: UserRead,
    ) -> VoiceCommandResponse:
        known = dict(session.known_fields)
        title, description = self.enrich_known_with_generated(session, known)
        category_id = session.category_id
        category_slug = session.category_slug
        if category_id is None:
            return self._responses.draft_missing_category(
                intent,
                draft={"known_fields": known, "category_id": None},
            )

        price = Decimal("0")
        price_val = known.get("price")
        if price_val is not None:
            try:
                price = Decimal(str(price_val))
            except InvalidOperation:
                price = Decimal("0")

        currency_raw = known.get("currency")
        currency = Currency.KGS
        if isinstance(currency_raw, str):
            try:
                currency = Currency(currency_raw.strip().upper())
            except ValueError:
                currency = Currency.KGS

        if session.listing_id:
            listing_row = await self._listings.get_listing(session.listing_id)
            mod_message = assistant_message_for_images(listing_row.images)
            if mod_message:
                preview = self.build_draft_preview(
                    category_id=int(category_id),
                    category_slug=category_slug,
                    category_name=session.category_name,
                    known_fields=known,
                    title=title,
                    description=description,
                )
                if mod_message == IMAGE_REJECTED_USER_MESSAGE:
                    return self._responses.image_moderation_rejected(
                        intent,
                        message=mod_message,
                        preview=preview,
                    )
                return self._responses.image_moderation_queue(
                    intent,
                    message=mod_message,
                    preview=preview,
                )
            session.real_photo_count = count_real_photos(listing_row.images)

        real_photos = session.real_photo_count
        needs_real = requires_real_photo(category_slug)
        can_placeholder = allows_placeholder_image(category_slug)

        if needs_real and real_photos < 1:
            body = ListingCreate(
                title=title.strip(),
                description=description,
                price=price,
                category_id=int(category_id),
                currency=currency,
                status=ListingStatus.draft,
            )
            created = await self._listings.create_listing(
                body,
                owner_id=current_user.id,
                known_fields=known,
            )
            session.listing_id = int(created.id)
            session.flow_stage = "publish_preview"
            preview = self.build_draft_preview(
                category_id=int(category_id),
                category_slug=category_slug,
                category_name=session.category_name,
                known_fields=known,
                title=title,
                description=description,
            )
            return self._responses.photo_publish_blocked(
                intent,
                message=PUBLISH_BLOCKED_NO_PHOTO,
                preview=preview,
                listing_payload=created.model_dump(mode="json"),
            )

        uses_placeholder = can_placeholder and real_photos < 1
        body = ListingCreate(
            title=title.strip(),
            description=description,
            price=price,
            category_id=int(category_id),
            currency=currency,
            status=ListingStatus.active,
            uses_placeholder_image=uses_placeholder,
        )
        created = await self._listings.create_listing(
            body,
            owner_id=current_user.id,
            known_fields=known,
        )
        listing_id = int(created.id)
        session.listing_id = listing_id
        session.flow_stage = "promotion"

        images = list(getattr(created, "images", None) or [])
        mod_message = assistant_message_for_images(images)
        if mod_message:
            preview = self.build_draft_preview(
                category_id=int(category_id),
                category_slug=category_slug,
                category_name=session.category_name,
                known_fields=known,
                title=title,
                description=description,
            )
            if mod_message == IMAGE_REJECTED_USER_MESSAGE:
                return self._responses.image_moderation_rejected(
                    intent,
                    message=mod_message,
                    preview=preview,
                )
            return self._responses.image_moderation_queue(
                intent,
                message=mod_message,
                preview=preview,
            )

        has_real_images = count_real_photos(images) > 0 or real_photos > 0
        photo_note = None
        if not has_real_images and can_placeholder:
            photo_note = PHOTO_REMINDER_TEXT

        offer = self._promotion.build_offer(listing_id)
        message = "Объявление опубликовано. " + (offer.message or "")
        return self._responses.listing_published(
            intent,
            listing_payload=created.model_dump(mode="json"),
            promotion_offer=offer,
            message=message,
            needs_photos=not has_real_images and needs_real,
            photo_reminder=photo_note,
        )

    async def handle_post_preview_message(
        self,
        intent: VoiceIntent,
        session: VoiceDialogueSession,
        text: str,
        current_user: UserRead,
    ) -> VoiceCommandResponse | None:
        if session.flow_stage == "promotion" and session.listing_id:
            return self._promotion.handle_response(
                intent,
                user=current_user,
                listing_id=session.listing_id,
                text=text,
            )

        if session.flow_stage == "publish_preview":
            if self.is_publish_confirmation(text):
                return await self.publish_confirmed(intent, session, current_user)
            if _PHOTO_ACK.search(text):
                session.photos_acknowledged = True
                return self._responses.photo_acknowledged(
                    intent,
                    message=(f"{self.PREVIEW_MESSAGE} {self.PUBLISH_PROMPT}"),
                    preview=self.build_draft_preview(
                        category_id=int(session.category_id or 0),
                        category_slug=session.category_slug,
                        category_name=session.category_name,
                        known_fields=session.known_fields,
                        title=session.generated_title or "",
                        description=session.generated_description or "",
                    ),
                )
            return self._responses.publish_confirmation_required(
                intent,
                message=f"Для публикации напишите «подтверждаю» или «опубликовать». {self.PUBLISH_PROMPT}",
            )

        return None


def _str_field(val: Any) -> str | None:
    if val is None:
        return None
    s = str(val).strip()
    return s or None
