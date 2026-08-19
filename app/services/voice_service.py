from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from app.core.exceptions import AppException
from app.models.enums import Currency
from app.schemas.saved_search import SavedSearchCreate
from app.schemas.user import UserRead
from app.schemas.voice import VoiceCommandRequest, VoiceCommandResponse, VoiceIntent
from app.services.category_intelligence_service import CategoryIntelligenceService
from app.services.listing_service import ListingService
from app.services.saved_search_service import SavedSearchService
from app.services.speech_to_text_service import SpeechToTextService
from app.services.voice_dialogue_manager import VoiceDialogueManager
from app.services.voice_intent_resolver import resolve_voice_intent
from app.services.voice_response_builder import VoiceResponseBuilder
from app.services.voice_session_store import VoiceSessionStoreProtocol, pending_voice_sessions


class VoiceService:
    """Thin orchestrator: STT → intent → dialogue / search / save."""

    def __init__(
        self,
        listing_service: ListingService,
        saved_search_service: SavedSearchService,
        speech_to_text: SpeechToTextService,
        category_intelligence: CategoryIntelligenceService | None = None,
        session_store: VoiceSessionStoreProtocol | None = None,
    ) -> None:
        store = session_store or pending_voice_sessions
        self._listings = listing_service
        self._saved_searches = saved_search_service
        self._stt = speech_to_text
        self._responses = VoiceResponseBuilder
        self._dialogue = VoiceDialogueManager(
            category_intelligence=category_intelligence,
            session_store=store,
            listing_service=listing_service,
        )

    @staticmethod
    def _validate_command_text(text: str) -> str:
        stripped = text.strip()
        if not stripped or len(stripped) > 1000:
            raise AppException("Некорректная длина текста", status_code=400)
        return stripped

    @staticmethod
    def _has_save_search_params(extracted: dict[str, Any]) -> bool:
        q = extracted.get("q")
        if isinstance(q, str) and q.strip():
            return True
        if extracted.get("min_price") is not None or extracted.get("max_price") is not None:
            return True
        if extracted.get("category_id") is not None:
            return True
        if extracted.get("currency") is not None:
            return True
        return False

    @staticmethod
    def _build_saved_search_query_params(extracted: dict[str, Any]) -> dict[str, Any]:
        qp: dict[str, Any] = {}
        q = extracted.get("q")
        if isinstance(q, str) and q.strip():
            qp["q"] = q.strip()
        for key in ("min_price", "max_price"):
            val = extracted.get(key)
            if val is not None:
                qp[key] = str(val)
        if extracted.get("category_id") is not None:
            qp["category_id"] = str(int(extracted["category_id"]))
        cur = extracted.get("currency")
        if isinstance(cur, str) and cur.strip():
            qp["currency"] = cur.strip().upper()
        return qp

    @staticmethod
    def _parse_currency(value: Any) -> Currency | None:
        if not isinstance(value, str):
            return None
        try:
            return Currency(value.strip().upper())
        except ValueError:
            return None

    async def _handle_save_search(
        self,
        intent: VoiceIntent,
        current_user: UserRead,
    ) -> VoiceCommandResponse:
        if not self._has_save_search_params(intent.extracted):
            return self._responses.save_search_missing_params(intent)
        qp = self._build_saved_search_query_params(intent.extracted)
        saved = await self._saved_searches.create_saved_search(
            SavedSearchCreate(query_params=qp),
            current_user.id,
        )
        return self._responses.save_search_saved(
            intent,
            saved.model_dump(mode="json"),
        )

    async def _handle_search_listings(self, intent: VoiceIntent) -> VoiceCommandResponse:
        ext = intent.extracted
        q = ext.get("q")
        q_clean = q.strip() if isinstance(q, str) else None
        category_id = ext.get("category_id")
        cid = int(category_id) if category_id is not None else None

        min_p = ext.get("min_price")
        max_p = ext.get("max_price")
        min_price: Decimal | None = None
        max_price: Decimal | None = None
        if min_p is not None:
            try:
                min_price = Decimal(str(min_p))
            except InvalidOperation:
                min_price = None
        if max_p is not None:
            try:
                max_price = Decimal(str(max_p))
            except InvalidOperation:
                max_price = None

        currency = self._parse_currency(ext.get("currency"))

        page = await self._listings.get_feed(
            q=q_clean,
            category_id=cid,
            min_price=min_price,
            max_price=max_price,
            currency=currency,
            status=None,
            limit=20,
            offset=0,
        )
        return self._responses.search_results(
            intent,
            [r.model_dump(mode="json") for r in page.items],
        )

    async def handle_audio(self, audio_bytes: bytes, current_user: UserRead) -> VoiceCommandResponse:
        text = await self._stt.transcribe(audio_bytes)
        return await self.handle_command(VoiceCommandRequest(text=text), current_user)

    async def handle_command(self, payload: VoiceCommandRequest, current_user: UserRead) -> VoiceCommandResponse:
        text = self._validate_command_text(payload.text)

        session = self._dialogue.get_pending_session(current_user.id)
        if session and not self._dialogue.is_new_command(text):
            return await self._dialogue.continue_dialogue(session, text, current_user)
        if session and self._dialogue.is_new_command(text):
            self._dialogue.clear_session(current_user.id)

        resolved = resolve_voice_intent(text)
        if resolved.ambiguous and resolved.ambiguity_message:
            return self._responses.intent_ambiguity(resolved.intent, resolved.ambiguity_message)

        intent = resolved.intent

        if intent.intent == "create_listing":
            return await self._dialogue.handle_create_listing(intent, text, current_user)

        if intent.intent == "save_search":
            return await self._handle_save_search(intent, current_user)

        if intent.intent == "search_listings":
            return await self._handle_search_listings(intent)

        return self._responses.unknown(intent)
