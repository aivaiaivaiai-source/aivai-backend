from __future__ import annotations

from app.models.category_enums import ModerationAction
from app.schemas.category_intelligence import CategoryDialogueResponse
from app.schemas.voice import VoiceCommandResponse, VoiceIntent
from app.services.voice_response_builder import VoiceResponseBuilder


class VoiceModerationFlow:
    @staticmethod
    def is_blocked(dialogue: CategoryDialogueResponse) -> bool:
        return dialogue.moderation_action == ModerationAction.block

    @staticmethod
    def is_queue(dialogue: CategoryDialogueResponse) -> bool:
        return dialogue.moderation_action == ModerationAction.moderation_queue

    @staticmethod
    def block_response(
        intent: VoiceIntent,
        dialogue: CategoryDialogueResponse,
    ) -> VoiceCommandResponse:
        return VoiceResponseBuilder.moderation_block(intent, dialogue)

    @staticmethod
    def queue_response(
        intent: VoiceIntent,
        dialogue: CategoryDialogueResponse,
        known_fields: dict[str, object],
    ) -> VoiceCommandResponse:
        return VoiceResponseBuilder.moderation_queue(intent, dialogue, known_fields)
