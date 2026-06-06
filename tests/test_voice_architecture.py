from __future__ import annotations

import pytest

from app.schemas.voice import VoiceCommandResponse, VoiceIntent
from app.services.voice_intent_resolver import resolve_voice_intent
from app.services.voice_moderation_flow import VoiceModerationFlow
from app.services.voice_response_builder import VoiceResponseBuilder
from app.services.voice_session_store import (
    InMemoryVoiceSessionStore,
    VoiceDialogueSession,
    VoiceSessionStoreProtocol,
)
from app.models.category_enums import CategoryFieldType, ModerationAction
from app.schemas.category_intelligence import (
    CategoryDialogueResponse,
    CategoryFieldRead,
    CategoryRoutingResult,
)


def test_kuplu_iphone_is_search_not_create() -> None:
    resolved = resolve_voice_intent("куплю айфон")
    assert resolved.intent.intent == "search_listings"
    assert resolved.ambiguous is False
    assert resolved.intent.extracted.get("q") == "айфон"


def test_prodayu_iphone_is_create() -> None:
    resolved = resolve_voice_intent("продаю айфон")
    assert resolved.intent.intent == "create_listing"
    assert resolved.ambiguous is False


def test_ambiguous_sell_and_buy() -> None:
    resolved = resolve_voice_intent("продаю и куплю айфон")
    assert resolved.ambiguous is True
    assert resolved.intent.intent == "unknown"
    assert resolved.ambiguity_message


def test_in_memory_store_implements_protocol() -> None:
    store: VoiceSessionStoreProtocol = InMemoryVoiceSessionStore(ttl_seconds=60.0)
    session = VoiceDialogueSession(user_id=7, seed_text="продаю камри")
    assert session.conversation_id
    assert session.created_at
    assert session.updated_at
    store.save(session)
    assert store.get(7) is not None
    store.clear(7)
    assert store.get(7) is None


def test_response_builder_clarification_schema() -> None:
    intent = VoiceIntent(intent="create_listing", confidence=0.8, extracted={})
    routing = CategoryRoutingResult(category_id=1, category_slug="x", category_name="X", confidence=0.9)
    dialogue = CategoryDialogueResponse(
        routing=routing,
        missing_core_fields=[
            CategoryFieldRead(
                field_key="city",
                label="Город",
                field_type=CategoryFieldType.city,
                is_required=True,
                sort_order=0,
                ai_hint="В каком городе?",
            ),
        ],
        next_question="В каком городе?",
        message="В каком городе?",
    )
    resp = VoiceResponseBuilder.clarification(intent, dialogue)
    VoiceCommandResponse.model_validate(resp.model_dump())
    assert resp.needs_clarification is True
    assert resp.next_question == "В каком городе?"


def test_moderation_block_does_not_imply_listing_created() -> None:
    intent = VoiceIntent(intent="create_listing", confidence=0.8, extracted={})
    routing = CategoryRoutingResult(category_id=1, confidence=0.9)
    dialogue = CategoryDialogueResponse(
        routing=routing,
        moderation_action=ModerationAction.block,
        message="Запрещено",
    )
    assert VoiceModerationFlow.is_blocked(dialogue)
    resp = VoiceModerationFlow.block_response(intent, dialogue)
    assert resp.moderation_required is True
    assert resp.data is not None
    assert "listing" not in (resp.data or {})
