from fastapi import APIRouter, Depends, Query

from app.api.deps import get_ai_agent_service, get_current_user
from app.core.ai_agent_policy import HISTORY_MAX_LIMIT, HISTORY_PAGE_SIZE
from app.models.ai_enums import AiAgentType
from app.schemas.ai_agent import (
    AiAgentInfo,
    AiMessageRead,
    AiSendMessageRequest,
    AiSendMessageResponse,
    AiSubscribeRequest,
    AiSubscriptionRead,
)
from app.schemas.user import UserRead
from app.services.ai_agent_service import AiAgentService

router = APIRouter()


@router.get("", response_model=list[AiAgentInfo])
async def list_ai_agents(
    service: AiAgentService = Depends(get_ai_agent_service),
    user: UserRead = Depends(get_current_user),
) -> list[AiAgentInfo]:
    return await service.list_agents(user.id)


@router.post("/subscribe", response_model=AiSubscriptionRead, status_code=201)
async def subscribe_ai_agent(
    body: AiSubscribeRequest,
    service: AiAgentService = Depends(get_ai_agent_service),
    user: UserRead = Depends(get_current_user),
) -> AiSubscriptionRead:
    return await service.subscribe(user.id, body.agent_type)


@router.post("/cancel", response_model=AiSubscriptionRead)
async def cancel_ai_agent(
    body: AiSubscribeRequest,
    service: AiAgentService = Depends(get_ai_agent_service),
    user: UserRead = Depends(get_current_user),
) -> AiSubscriptionRead:
    return await service.cancel(user.id, body.agent_type)


@router.get("/{agent_type}/subscription", response_model=AiSubscriptionRead | None)
async def get_ai_subscription(
    agent_type: AiAgentType,
    service: AiAgentService = Depends(get_ai_agent_service),
    user: UserRead = Depends(get_current_user),
) -> AiSubscriptionRead | None:
    return await service.get_subscription(user.id, agent_type)


@router.get("/{agent_type}/history", response_model=list[AiMessageRead])
async def get_ai_history(
    agent_type: AiAgentType,
    before_id: int | None = Query(default=None, ge=1),
    after_id: int | None = Query(default=None, ge=1),
    limit: int = Query(default=HISTORY_PAGE_SIZE, ge=1, le=HISTORY_MAX_LIMIT),
    service: AiAgentService = Depends(get_ai_agent_service),
    user: UserRead = Depends(get_current_user),
) -> list[AiMessageRead]:
    return await service.history(
        user.id,
        agent_type,
        before_id=before_id,
        after_id=after_id,
        limit=limit,
    )


@router.post("/{agent_type}/message", response_model=AiSendMessageResponse)
async def send_ai_message(
    agent_type: AiAgentType,
    body: AiSendMessageRequest,
    service: AiAgentService = Depends(get_ai_agent_service),
    user: UserRead = Depends(get_current_user),
) -> AiSendMessageResponse:
    return await service.send_message(user.id, agent_type, body.content)


@router.delete("/{agent_type}/messages/{message_id}", status_code=204)
async def delete_ai_message(
    agent_type: AiAgentType,
    message_id: int,
    service: AiAgentService = Depends(get_ai_agent_service),
    user: UserRead = Depends(get_current_user),
) -> None:
    await service.delete_message(user.id, agent_type, message_id)
