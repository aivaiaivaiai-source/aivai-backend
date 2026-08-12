from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Any

from app.models.enums import Currency, ListingStatus
from app.schemas.category_intelligence import CategoryDialogueRequest, CategoryDialogueResponse
from app.schemas.listing import ListingCreate
from app.schemas.user import UserRead
from app.schemas.voice import VoiceCommandResponse, VoiceIntent
from app.services.category_intelligence_service import CategoryIntelligenceService
from app.services.listing_creation_assistant import ListingCreationAssistant
from app.services.listing_service import ListingService
from app.services.voice_field_extractor import extract_field_answer, parse_price_value
from app.services.voice_moderation_flow import VoiceModerationFlow
from app.services.voice_response_builder import VoiceResponseBuilder
from app.services.voice_session_store import (
    VoiceDialogueSession,
    VoiceSessionStoreProtocol,
)

_NEW_COMMAND = re.compile(
    r"(?:созда(?:ть|й)\s+объявлен|новое\s+объявлени|найди|найти|поиск|покажи\s+объявлен"
    r"|сохран(?:ить|и)\s+(?:этот\s+)?поиск|save\s+(?:this\s+)?search)",
    re.IGNORECASE,
)


class VoiceDialogueManager:
    def __init__(
        self,
        *,
        category_intelligence: CategoryIntelligenceService | None,
        session_store: VoiceSessionStoreProtocol,
        listing_service: ListingService,
    ) -> None:
        self._category_intel = category_intelligence
        self._sessions = session_store
        self._listings = listing_service
        self._assistant = ListingCreationAssistant(listing_service)
        self._responses = VoiceResponseBuilder
        self._moderation = VoiceModerationFlow

    @staticmethod
    def is_new_command(text: str) -> bool:
        return bool(_NEW_COMMAND.search(text))

    @staticmethod
    def merge_voice_extracted(known: dict[str, Any], extracted: dict[str, Any]) -> dict[str, Any]:
        merged = dict(known)
        for key, val in extracted.items():
            if val is None:
                continue
            if key == "category_id" and merged.get("category_id") is None:
                merged["category_id"] = val
            elif key == "price" and not merged.get("price"):
                merged["price"] = val
            elif key == "currency" and not merged.get("currency"):
                merged["currency"] = val
            elif key == "title" and not merged.get("title"):
                merged["title"] = val
        return merged

    def get_pending_session(self, user_id: int) -> VoiceDialogueSession | None:
        return self._sessions.get(user_id)

    def clear_session(self, user_id: int) -> None:
        self._sessions.clear(user_id)

    async def continue_dialogue(
        self,
        session: VoiceDialogueSession,
        text: str,
        current_user: UserRead,
    ) -> VoiceCommandResponse:
        intent = VoiceIntent(
            intent=session.intent_name,
            confidence=0.85,
            extracted=dict(session.voice_extracted),
        )
        post_preview = await self._assistant.handle_post_preview_message(
            intent,
            session,
            text,
            current_user,
        )
        if post_preview is not None:
            if session.flow_stage != "promotion":
                self._sessions.save(session)
            else:
                self._sessions.clear(current_user.id)
            return post_preview

        known = dict(session.known_fields)
        field_key = session.awaiting_field_key
        if field_key:
            answer = extract_field_answer(field_key, text)
            if answer is not None:
                known[field_key] = answer
            elif field_key == "price":
                price = parse_price_value(text)
                if price:
                    known["price"] = price

        intent = VoiceIntent(
            intent=session.intent_name,
            confidence=0.85,
            extracted=dict(session.voice_extracted),
        )
        return await self.handle_create_listing(
            intent,
            text,
            current_user,
            known_fields=known,
            session=session,
        )

    async def _run_category_dialogue(
        self,
        text: str,
        known_fields: dict[str, Any],
    ) -> CategoryDialogueResponse | None:
        if self._category_intel is None:
            return None
        return await self._category_intel.dialogue(
            CategoryDialogueRequest(text=text, known_fields=known_fields),
        )

    async def handle_create_listing(
        self,
        intent: VoiceIntent,
        text: str,
        current_user: UserRead,
        *,
        known_fields: dict[str, Any] | None = None,
        session: VoiceDialogueSession | None = None,
    ) -> VoiceCommandResponse:
        known = self.merge_voice_extracted(known_fields or {}, intent.extracted)

        if self._category_intel is None:
            return await self._create_listing_legacy(intent, current_user)

        dialogue = await self._run_category_dialogue(text, known)
        if dialogue is None:
            return await self._create_listing_legacy(intent, current_user)

        if not dialogue.in_marketplace_domain:
            return self._responses.out_of_domain(intent, dialogue.message)

        if self._moderation.is_blocked(dialogue):
            if session:
                self.clear_session(current_user.id)
            return self._moderation.block_response(intent, dialogue)

        routing = dialogue.routing
        if routing.mode in ("clarification", "suggestion") or routing.category_id is None:
            suggestions: list[dict[str, str]] = []
            if routing.category_slug and routing.category_name:
                suggestions.append(
                    {"slug": routing.category_slug, "name": routing.category_name},
                )
            resp = self._responses.clarification(
                intent,
                dialogue,
                suggestions=suggestions,
                known_fields=known if session else None,
            )
            if session is None and routing.category_id:
                self._persist_session(current_user.id, intent, text, dialogue, known)
            elif session:
                self._update_session_from_dialogue(session, dialogue, known)
                self._sessions.save(session)
            return resp

        if dialogue.missing_core_fields:
            if session is None:
                self._persist_session(current_user.id, intent, text, dialogue, known)
            else:
                self._update_session_from_dialogue(session, dialogue, known)
                self._sessions.save(session)
            return self._responses.clarification(intent, dialogue, known_fields=known)

        if self._moderation.is_queue(dialogue):
            self.clear_session(current_user.id)
            return self._moderation.queue_response(intent, dialogue, known)

        if session is None:
            session = self._persist_session(current_user.id, intent, text, dialogue, known)
        else:
            self._update_session_from_dialogue(session, dialogue, known)
        self._sessions.save(session)
        return self._assistant.ready_for_preview(intent, session, known)

    def _persist_session(
        self,
        user_id: int,
        intent: VoiceIntent,
        text: str,
        dialogue: CategoryDialogueResponse,
        known: dict[str, Any],
    ) -> VoiceDialogueSession:
        missing = dialogue.missing_core_fields
        first_key = missing[0].field_key if missing else None
        session = VoiceDialogueSession(
            user_id=user_id,
            intent_name=intent.intent,
            seed_text=text,
            category_id=dialogue.routing.category_id,
            category_slug=dialogue.routing.category_slug,
            category_name=dialogue.routing.category_name,
            known_fields=dict(known),
            missing_field_keys=self._responses.missing_keys(missing),
            awaiting_field_key=first_key,
            last_question=dialogue.next_question,
            voice_extracted=dict(intent.extracted),
            moderation_action=dialogue.moderation_action.value,
            moderation_reason=dialogue.moderation_reason,
        )
        self._sessions.save(session)
        return session

    def _update_session_from_dialogue(
        self,
        session: VoiceDialogueSession,
        dialogue: CategoryDialogueResponse,
        known: dict[str, Any],
    ) -> None:
        session.category_id = dialogue.routing.category_id
        session.category_slug = dialogue.routing.category_slug
        session.category_name = dialogue.routing.category_name
        session.known_fields = dict(known)
        missing = dialogue.missing_core_fields
        session.missing_field_keys = self._responses.missing_keys(missing)
        session.awaiting_field_key = missing[0].field_key if missing else None
        session.last_question = dialogue.next_question
        session.moderation_action = dialogue.moderation_action.value
        session.moderation_reason = dialogue.moderation_reason

    @staticmethod
    def _parse_currency(value: Any) -> Currency | None:
        if not isinstance(value, str):
            return None
        try:
            return Currency(value.strip().upper())
        except ValueError:
            return None

    async def _create_listing_from_fields(
        self,
        intent: VoiceIntent,
        category_id: int | None,
        known: dict[str, Any],
        current_user: UserRead,
    ) -> VoiceCommandResponse:
        if category_id is None:
            return self._responses.draft_missing_category(
                intent,
                draft={"known_fields": known, "category_id": None},
            )

        title = known.get("title") if isinstance(known.get("title"), str) else None
        if not (title and str(title).strip()):
            brand = known.get("brand") or known.get("vehicle_brand")
            model = known.get("model") or known.get("vehicle_model")
            if brand or model:
                title = f"{brand or ''} {model or ''}".strip()
            else:
                title = "Голосовое объявление"

        price_val = known.get("price")
        price = Decimal("0")
        if price_val is not None:
            try:
                price = Decimal(str(price_val))
            except InvalidOperation:
                price = Decimal("0")

        currency = self._parse_currency(known.get("currency")) or Currency.KGS

        body = ListingCreate(
            title=str(title).strip(),
            description=known.get("description") if isinstance(known.get("description"), str) else None,
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
        return self._responses.listing_created(
            intent,
            created.model_dump(mode="json"),
            known_fields=known,
        )

    async def _create_listing_legacy(
        self,
        intent: VoiceIntent,
        current_user: UserRead,
    ) -> VoiceCommandResponse:
        ext = intent.extracted
        category_id = ext.get("category_id")
        if category_id is None:
            draft: dict[str, Any] = {
                "title": ext.get("title"),
                "description": ext.get("description"),
                "price": ext.get("price"),
                "currency": ext.get("currency"),
                "category_id": None,
                "status": ListingStatus.draft.value,
            }
            return self._responses.draft_missing_category(intent, draft=draft)

        title = ext.get("title") if isinstance(ext.get("title"), str) else None
        if not (title and title.strip()):
            title = "Голосовое объявление"

        price_val = ext.get("price")
        price = Decimal("0")
        if price_val is not None:
            try:
                price = Decimal(str(price_val))
            except InvalidOperation:
                price = Decimal("0")

        currency = self._parse_currency(ext.get("currency")) or Currency.KGS

        body = ListingCreate(
            title=title.strip(),
            description=ext.get("description") if isinstance(ext.get("description"), str) else None,
            price=price,
            category_id=int(category_id),
            currency=currency,
            status=ListingStatus.draft,
        )
        created = await self._listings.create_listing(
            body,
            owner_id=current_user.id,
            known_fields=ext,
        )
        return self._responses.listing_created(intent, created.model_dump(mode="json"))
