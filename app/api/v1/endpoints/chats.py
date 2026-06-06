from fastapi import APIRouter, Depends, Query

from app.api.deps import get_chat_service, get_current_user
from app.core.constants import MAX_LIMIT
from app.schemas.chat import ChatRead
from app.schemas.message import MessageCreate, MessageRead
from app.schemas.user import UserRead
from app.services.chat_service import ChatService

router = APIRouter()


@router.post("/listings/{listing_id}", response_model=ChatRead, status_code=201)
async def open_chat_for_listing(
    listing_id: int,
    service: ChatService = Depends(get_chat_service),
    user: UserRead = Depends(get_current_user),
) -> ChatRead:
    return await service.get_or_create_chat_for_listing(
        listing_id,
        current_user_id=user.id,
    )


@router.get("", response_model=list[ChatRead])
async def list_my_chats(
    service: ChatService = Depends(get_chat_service),
    user: UserRead = Depends(get_current_user),
) -> list[ChatRead]:
    return await service.list_chats_for_user(current_user_id=user.id)


@router.get("/{chat_id}/messages", response_model=list[MessageRead])
async def get_chat_messages(
    chat_id: int,
    service: ChatService = Depends(get_chat_service),
    user: UserRead = Depends(get_current_user),
    limit: int = Query(default=20, ge=1, le=MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
) -> list[MessageRead]:
    return await service.list_messages(
        chat_id,
        current_user_id=user.id,
        limit=limit,
        offset=offset,
    )


@router.post("/{chat_id}/messages", response_model=MessageRead, status_code=201)
async def send_chat_message(
    chat_id: int,
    body: MessageCreate,
    service: ChatService = Depends(get_chat_service),
    user: UserRead = Depends(get_current_user),
) -> MessageRead:
    return await service.send_message(
        chat_id,
        current_user_id=user.id,
        text=body.text,
        media_ids=body.media_ids,
    )
