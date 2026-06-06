from fastapi import APIRouter, Depends, Query

from app.api.deps import get_assistant_service, get_current_user
from app.schemas.assistant import (
    AssistantMessageRead,
    AssistantMessageRequest,
    AssistantMessageResponse,
)
from app.schemas.user import UserRead
from app.services.assistant_service import AssistantService

router = APIRouter()


@router.post("/message", response_model=AssistantMessageResponse)
async def post_assistant_message(
    body: AssistantMessageRequest,
    service: AssistantService = Depends(get_assistant_service),
    user: UserRead = Depends(get_current_user),
) -> AssistantMessageResponse:
    return await service.handle_message(body, user)


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=list[AssistantMessageRead],
)
async def get_conversation_messages(
    conversation_id: int,
    limit: int = Query(default=50, ge=1, le=200),
    service: AssistantService = Depends(get_assistant_service),
    user: UserRead = Depends(get_current_user),
) -> list[AssistantMessageRead]:
    return await service.get_conversation_history(conversation_id, user.id, limit=limit)
