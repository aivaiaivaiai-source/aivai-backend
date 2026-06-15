"""Service dependency providers.

Each request gets one ``AsyncSession`` from ``get_db``; repositories and services
share that session for the unit of work. Map ``AppException`` subclasses to HTTP
responses via handlers registered on the FastAPI app (see ``app.main``).
"""

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.exceptions import UnauthorizedError
from app.core.security import decode_token
from app.db.session import get_db
from app.repositories.chat_repository import ChatRepository
from app.repositories.category_alias_repository import CategoryAliasRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.category_moderation_rule_repository import CategoryModerationRuleRepository
from app.repositories.category_routing_rule_repository import CategoryRoutingRuleRepository
from app.repositories.vehicle_repository import (
    VehicleAliasRepository,
    VehicleBrandRepository,
    VehicleModelRepository,
)
from app.repositories.health_repository import HealthRepository
from app.repositories.listing_repository import ListingRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.media_repository import MediaRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.saved_search_repository import SavedSearchRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserRead
from app.services.assistant_conversation_service import AssistantConversationService
from app.services.assistant_service import AssistantService, build_assistant_conversation_service
from app.services.assistant_voice_service import AssistantVoiceService
from app.services.text_to_speech_service import OpenAITTSService, TextToSpeechService
from app.services.tts_audio_storage import TtsAudioStorage
from app.services.auth_service import AuthService
from app.services.chat_service import ChatService
from app.services.category_intelligence_service import CategoryIntelligenceService
from app.services.category_service import CategoryService
from app.services.health_service import HealthService
from app.services.listing_service import ListingService
from app.services.image_moderation_pipeline import build_image_moderation_pipeline
from app.services.media_service import MediaService
from app.services.notification_service import NotificationService
from app.services.saved_search_service import SavedSearchService
from app.services.speech_to_text_service import SpeechToTextService, WhisperSpeechToTextService
from app.services.storage_service import StorageService
from app.services.user_service import UserService
from app.services.vehicle_catalog_service import VehicleCatalogService
from app.services.voice_service import VoiceService


bearer_scheme = HTTPBearer(auto_error=False)


def get_user_service(session: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(session, UserRepository(session))


def get_auth_service(session: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(UserService(session, UserRepository(session)))


async def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    user_service: UserService = Depends(get_user_service),
) -> UserRead:
    settings = get_settings()
    if creds is None or creds.scheme.lower() != "bearer":
        raise UnauthorizedError("Not authenticated.")

    try:
        payload = decode_token(creds.credentials, settings=settings)
    except JWTError:
        raise UnauthorizedError("Invalid or expired token.")

    if payload.get("type") != "access":
        raise UnauthorizedError("Invalid token type.")

    raw_sub = payload.get("sub")
    if raw_sub is None:
        raise UnauthorizedError("Invalid token payload.")

    try:
        user_id = int(raw_sub)
    except (TypeError, ValueError):
        raise UnauthorizedError("Invalid subject in token.")

    user = await user_service.get_user_by_id(user_id)
    if user is None:
        raise UnauthorizedError("User not found.")
    if not user.is_active:
        raise UnauthorizedError("User is inactive.")

    return user


def get_chat_service(session: AsyncSession = Depends(get_db)) -> ChatService:
    settings = get_settings()
    return ChatService(
        session,
        ChatRepository(session),
        MessageRepository(session),
        ListingRepository(session),
        MediaRepository(session),
        StorageService(settings),
    )


def get_listing_service(session: AsyncSession = Depends(get_db)) -> ListingService:
    return ListingService(
        session,
        ListingRepository(session),
        CategoryRepository(session),
        NotificationService(
            session,
            NotificationRepository(session),
            SavedSearchRepository(session),
        ),
    )


def get_notification_service(session: AsyncSession = Depends(get_db)) -> NotificationService:
    return NotificationService(
        session,
        NotificationRepository(session),
        SavedSearchRepository(session),
    )


def get_media_service(session: AsyncSession = Depends(get_db)) -> MediaService:
    settings = get_settings()
    media_repo = MediaRepository(session)
    storage = StorageService(settings)
    return MediaService(
        session,
        media_repo,
        ListingRepository(session),
        storage,
        moderation_pipeline=build_image_moderation_pipeline(
            session,
            media_repo,
            storage,
        ),
    )


def get_category_service(session: AsyncSession = Depends(get_db)) -> CategoryService:
    return CategoryService(CategoryRepository(session))


def get_vehicle_catalog_service(session: AsyncSession = Depends(get_db)) -> VehicleCatalogService:
    return VehicleCatalogService(
        VehicleBrandRepository(session),
        VehicleModelRepository(session),
    )


def get_category_intelligence_service(
    session: AsyncSession = Depends(get_db),
) -> CategoryIntelligenceService:
    return CategoryIntelligenceService(
        CategoryRepository(session),
        CategoryAliasRepository(session),
        CategoryRoutingRuleRepository(session),
        CategoryModerationRuleRepository(session),
        VehicleAliasRepository(session),
    )


def get_saved_search_service(session: AsyncSession = Depends(get_db)) -> SavedSearchService:
    return SavedSearchService(session, SavedSearchRepository(session))


def get_speech_to_text_service(settings: Settings = Depends(get_settings)) -> SpeechToTextService:
    return WhisperSpeechToTextService(settings)


def get_text_to_speech_service(settings: Settings = Depends(get_settings)) -> TextToSpeechService:
    return OpenAITTSService(settings)


def get_tts_audio_storage(settings: Settings = Depends(get_settings)) -> TtsAudioStorage:
    return TtsAudioStorage(settings)


def get_assistant_voice_service(
    tts: TextToSpeechService = Depends(get_text_to_speech_service),
    storage: TtsAudioStorage = Depends(get_tts_audio_storage),
) -> AssistantVoiceService:
    return AssistantVoiceService(tts, storage)


def get_voice_service(
    listing_service: ListingService = Depends(get_listing_service),
    saved_search_service: SavedSearchService = Depends(get_saved_search_service),
    speech_to_text: SpeechToTextService = Depends(get_speech_to_text_service),
    category_intelligence: CategoryIntelligenceService = Depends(get_category_intelligence_service),
) -> VoiceService:
    return VoiceService(
        listing_service,
        saved_search_service,
        speech_to_text,
        category_intelligence=category_intelligence,
    )


def get_assistant_conversation_service(
    session: AsyncSession = Depends(get_db),
) -> AssistantConversationService:
    return build_assistant_conversation_service(session)


def get_assistant_service(
    session: AsyncSession = Depends(get_db),
    voice_service: VoiceService = Depends(get_voice_service),
    conversation_service: AssistantConversationService = Depends(get_assistant_conversation_service),
    assistant_voice_service: AssistantVoiceService = Depends(get_assistant_voice_service),
) -> AssistantService:
    return AssistantService(session, voice_service, conversation_service, assistant_voice_service)


def get_health_service(session: AsyncSession = Depends(get_db)) -> HealthService:
    return HealthService(HealthRepository(session))
