from __future__ import annotations

from typing import Any

from app.schemas.category_intelligence import CategoryDialogueResponse
from app.schemas.listing_assistant import DraftPreview, PromotionOffer, PromotionResult
from app.schemas.voice import VoiceCommandResponse, VoiceDialogueState, VoiceIntent
from app.services.voice_session_store import VoiceDialogueSession


class VoiceResponseBuilder:
    @staticmethod
    def field_dicts(missing: list[Any]) -> list[dict[str, Any]]:
        return [f.model_dump(mode="json") for f in missing]

    @staticmethod
    def missing_keys(missing: list[Any]) -> list[str]:
        return [f.field_key for f in missing]

    @classmethod
    def dialogue_state_from_session(cls, session: VoiceDialogueSession) -> VoiceDialogueState:
        return VoiceDialogueState(
            category_id=session.category_id,
            category_slug=session.category_slug,
            category_name=session.category_name,
            known_fields=dict(session.known_fields),
            missing_fields=list(session.missing_field_keys),
            awaiting_field=session.awaiting_field_key,
        )

    @classmethod
    def dialogue_state_from_response(
        cls,
        dialogue: CategoryDialogueResponse,
        *,
        known_fields: dict[str, Any] | None = None,
    ) -> VoiceDialogueState:
        missing = dialogue.missing_core_fields
        return VoiceDialogueState(
            category_id=dialogue.routing.category_id,
            category_slug=dialogue.routing.category_slug,
            category_name=dialogue.routing.category_name,
            known_fields=dict(known_fields or {}),
            missing_fields=cls.missing_keys(missing),
            awaiting_field=missing[0].field_key if missing else None,
        )

    @classmethod
    def clarification(
        cls,
        intent: VoiceIntent,
        dialogue: CategoryDialogueResponse,
        *,
        suggestions: list[dict[str, str]] | None = None,
        known_fields: dict[str, Any] | None = None,
    ) -> VoiceCommandResponse:
        missing = dialogue.missing_core_fields
        next_q = dialogue.next_question or dialogue.message
        return VoiceCommandResponse(
            intent=intent,
            message=next_q,
            data={"routing": dialogue.routing.model_dump(mode="json")},
            needs_clarification=True,
            missing_fields=cls.field_dicts(missing),
            next_question=next_q,
            suggestions=suggestions or [],
            dialogue=cls.dialogue_state_from_response(dialogue, known_fields=known_fields),
        )

    @classmethod
    def intent_ambiguity(cls, intent: VoiceIntent, message: str) -> VoiceCommandResponse:
        return VoiceCommandResponse(
            intent=intent,
            message=message,
            data=None,
            needs_clarification=True,
            next_question=message,
        )

    @classmethod
    def moderation_block(
        cls,
        intent: VoiceIntent,
        dialogue: CategoryDialogueResponse,
    ) -> VoiceCommandResponse:
        return VoiceCommandResponse(
            intent=intent,
            message=dialogue.message,
            data={"routing": dialogue.routing.model_dump(mode="json")},
            moderation_required=True,
            moderation_reason=dialogue.moderation_reason,
        )

    @classmethod
    def moderation_queue(
        cls,
        intent: VoiceIntent,
        dialogue: CategoryDialogueResponse,
        known_fields: dict[str, Any],
    ) -> VoiceCommandResponse:
        return VoiceCommandResponse(
            intent=intent,
            message=dialogue.message,
            data={
                "routing": dialogue.routing.model_dump(mode="json"),
                "known_fields": known_fields,
            },
            moderation_required=True,
            moderation_reason=dialogue.moderation_reason,
        )

    @classmethod
    def out_of_domain(cls, intent: VoiceIntent, message: str) -> VoiceCommandResponse:
        return VoiceCommandResponse(intent=intent, message=message, data=None)

    @classmethod
    def draft_missing_category(
        cls,
        intent: VoiceIntent,
        *,
        draft: dict[str, Any],
    ) -> VoiceCommandResponse:
        return VoiceCommandResponse(
            intent=intent,
            message="Я подготовил черновик. Нужно выбрать категорию.",
            data={"draft": draft},
            needs_clarification=True,
        )

    @classmethod
    def listing_created(
        cls,
        intent: VoiceIntent,
        listing_payload: dict[str, Any],
        *,
        known_fields: dict[str, Any] | None = None,
    ) -> VoiceCommandResponse:
        data: dict[str, Any] = {"listing": listing_payload}
        if known_fields is not None:
            data["known_fields"] = known_fields
        return VoiceCommandResponse(
            intent=intent,
            message="Объявление создано.",
            data=data,
        )

    @classmethod
    def search_results(
        cls,
        intent: VoiceIntent,
        listings: list[dict[str, Any]],
    ) -> VoiceCommandResponse:
        has_rows = bool(listings)
        return VoiceCommandResponse(
            intent=intent,
            message="Найдены объявления по запросу." if has_rows else "По запросу ничего не найдено.",
            data={"listings": listings},
            suggest_save_search=not has_rows,
        )

    @classmethod
    def save_search_saved(cls, intent: VoiceIntent, payload: dict[str, Any]) -> VoiceCommandResponse:
        return VoiceCommandResponse(
            intent=intent,
            message="Поиск сохранён.",
            data={"saved_search": payload},
        )

    @classmethod
    def save_search_missing_params(cls, intent: VoiceIntent) -> VoiceCommandResponse:
        return VoiceCommandResponse(
            intent=intent,
            message="Сначала выполните поиск или уточните параметры поиска.",
            data=None,
        )

    @classmethod
    def unknown(cls, intent: VoiceIntent) -> VoiceCommandResponse:
        return VoiceCommandResponse(
            intent=intent,
            message="Команда не распознана. Попробуйте сформулировать иначе.",
            data=None,
        )

    @classmethod
    def draft_preview(
        cls,
        intent: VoiceIntent,
        *,
        preview: DraftPreview,
        message: str,
        needs_photos: bool = True,
        real_photo_required: bool = False,
    ) -> VoiceCommandResponse:
        return VoiceCommandResponse(
            intent=intent,
            message=message,
            data={"draft_preview": preview.model_dump(mode="json")},
            draft_preview=preview,
            needs_photos=needs_photos,
            real_photo_required=real_photo_required or preview.real_photo_required,
            publish_confirmation_required=True,
            next_question="Подтвердите публикацию, когда будете готовы.",
        )

    @classmethod
    def image_moderation_rejected(
        cls,
        intent: VoiceIntent,
        *,
        message: str,
        preview: DraftPreview | None = None,
    ) -> VoiceCommandResponse:
        data: dict[str, Any] = {"reason": "image_rejected"}
        if preview is not None:
            data["draft_preview"] = preview.model_dump(mode="json")
        return VoiceCommandResponse(
            intent=intent,
            message=message,
            data=data,
            draft_preview=preview,
            needs_photos=True,
            publish_confirmation_required=True,
            publish_blocked_missing_photo=True,
        )

    @classmethod
    def image_moderation_queue(
        cls,
        intent: VoiceIntent,
        *,
        message: str,
        preview: DraftPreview | None = None,
    ) -> VoiceCommandResponse:
        data: dict[str, Any] = {"reason": "image_moderation_queue"}
        if preview is not None:
            data["draft_preview"] = preview.model_dump(mode="json")
        return VoiceCommandResponse(
            intent=intent,
            message=message,
            data=data,
            draft_preview=preview,
            needs_photos=True,
            publish_confirmation_required=True,
        )

    @classmethod
    def photo_publish_blocked(
        cls,
        intent: VoiceIntent,
        *,
        message: str,
        preview: DraftPreview,
        listing_payload: dict[str, Any] | None = None,
    ) -> VoiceCommandResponse:
        data: dict[str, Any] = {
            "draft_preview": preview.model_dump(mode="json"),
            "reason": "missing_real_photo",
        }
        if listing_payload is not None:
            data["listing"] = listing_payload
        return VoiceCommandResponse(
            intent=intent,
            message=message,
            data=data,
            draft_preview=preview,
            needs_photos=True,
            real_photo_required=True,
            publish_confirmation_required=True,
            publish_blocked_missing_photo=True,
        )

    @classmethod
    def publish_confirmation_required(
        cls,
        intent: VoiceIntent,
        *,
        message: str,
    ) -> VoiceCommandResponse:
        return VoiceCommandResponse(
            intent=intent,
            message=message,
            publish_confirmation_required=True,
        )

    @classmethod
    def photo_acknowledged(
        cls,
        intent: VoiceIntent,
        *,
        message: str,
        preview: DraftPreview,
    ) -> VoiceCommandResponse:
        return VoiceCommandResponse(
            intent=intent,
            message=message,
            draft_preview=preview,
            needs_photos=True,
            publish_confirmation_required=True,
            data={"draft_preview": preview.model_dump(mode="json")},
        )

    @classmethod
    def listing_published(
        cls,
        intent: VoiceIntent,
        *,
        listing_payload: dict[str, Any],
        promotion_offer: PromotionOffer,
        message: str,
        needs_photos: bool = False,
        photo_reminder: str | None = None,
    ) -> VoiceCommandResponse:
        data: dict[str, Any] = {"listing": listing_payload}
        if photo_reminder:
            data["photo_reminder"] = photo_reminder
        return VoiceCommandResponse(
            intent=intent,
            message=message,
            data=data,
            needs_photos=needs_photos,
            promotion_offer=promotion_offer,
        )

    @classmethod
    def promotion_pending(
        cls,
        intent: VoiceIntent,
        *,
        offer: PromotionOffer,
        message: str,
    ) -> VoiceCommandResponse:
        return VoiceCommandResponse(
            intent=intent,
            message=message,
            promotion_offer=offer,
            publish_confirmation_required=False,
        )

    @classmethod
    def promotion_declined(cls, intent: VoiceIntent) -> VoiceCommandResponse:
        return VoiceCommandResponse(
            intent=intent,
            message="Хорошо, продвижение можно подключить позже в кабинете.",
            data=None,
        )

    @classmethod
    def promotion_activated(
        cls,
        intent: VoiceIntent,
        result: PromotionResult,
        *,
        listing_id: int,
    ) -> VoiceCommandResponse:
        return VoiceCommandResponse(
            intent=intent,
            message=result.message,
            data={
                "promotion": result.model_dump(mode="json"),
                "listing_id": listing_id,
            },
        )

    @classmethod
    def topup_required(
        cls,
        intent: VoiceIntent,
        result: PromotionResult,
        *,
        listing_id: int,
    ) -> VoiceCommandResponse:
        return VoiceCommandResponse(
            intent=intent,
            message=result.message,
            data={
                "promotion": result.model_dump(mode="json"),
                "listing_id": listing_id,
                "topup_required": True,
                "balance": result.balance,
                "required_amount": result.required_amount,
            },
        )
