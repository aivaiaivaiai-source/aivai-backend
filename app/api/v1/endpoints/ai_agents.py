from fastapi import APIRouter, Depends, Query

from app.api.deps import get_ai_agent_service, get_current_user
from app.models.enums import AiAgentType
from app.schemas.ai_agent import (
    AiAgentInfo,
    AiMessageOut,
    AiSendMessageRequest,
    AiSubscribeRequest,
    AiSubscriptionInfo,
)
from app.schemas.user import UserRead
from app.services.ai_agent_service import AiAgentService

router = APIRouter()


@router.get("", response_model=list[AiAgentInfo])
async def list_agents(
    service: AiAgentService = Depends(get_ai_agent_service),
    user: UserRead = Depends(get_current_user),
) -> list[dict]:
    return await service.list_agents(user.id)


@router.post("/subscribe", response_model=AiSubscriptionInfo)
async def subscribe(
    body: AiSubscribeRequest,
    service: AiAgentService = Depends(get_ai_agent_service),
    user: UserRead = Depends(get_current_user),
) -> AiSubscriptionInfo:
    from app.services.ai_agent_service import AiAgentPolicy

    agent_type = AiAgentType(body.agent_type)
    sub = await service.subscribe(user.id, agent_type)
    return AiSubscriptionInfo(
        id=sub.id,
        status=sub.status.value,
        starts_at=sub.starts_at,
        expires_at=sub.expires_at,
        messages_today=sub.messages_today,
        max_messages_day=AiAgentPolicy.MAX_MSG_PER_DAY,
    )


@router.get("/{agent_type}/history", response_model=list[AiMessageOut])
async def get_history(
    agent_type: AiAgentType,
    service: AiAgentService = Depends(get_ai_agent_service),
    user: UserRead = Depends(get_current_user),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[AiMessageOut]:
    messages = await service.get_history(user.id, agent_type, limit=limit, offset=offset)
    return [
        AiMessageOut(
            id=m.id,
            role=m.role.value,
            content=m.content,
            message_type=m.message_type.value,
            metadata_json=m.metadata_json,
            created_at=m.created_at,
        )
        for m in messages
    ]


@router.post("/{agent_type}/message", response_model=list[AiMessageOut])
async def send_message(
    agent_type: AiAgentType,
    body: AiSendMessageRequest,
    service: AiAgentService = Depends(get_ai_agent_service),
    user: UserRead = Depends(get_current_user),
) -> list[AiMessageOut]:
    messages = await service.send_message(user.id, agent_type, body.text)
    return [
        AiMessageOut(
            id=m.id,
            role=m.role.value,
            content=m.content,
            message_type=m.message_type.value,
            metadata_json=m.metadata_json,
            created_at=m.created_at,
        )
        for m in messages
    ]


@router.get("/{agent_type}/subscription", response_model=AiSubscriptionInfo | None)
async def check_subscription(
    agent_type: AiAgentType,
    service: AiAgentService = Depends(get_ai_agent_service),
    user: UserRead = Depends(get_current_user),
) -> AiSubscriptionInfo | None:
    from app.services.ai_agent_service import AiAgentPolicy

    sub = await service.check_subscription(user.id, agent_type)
    if sub is None:
        return None
    return AiSubscriptionInfo(
        id=sub.id,
        status=sub.status.value,
        starts_at=sub.starts_at,
        expires_at=sub.expires_at,
        messages_today=sub.messages_today,
        max_messages_day=AiAgentPolicy.MAX_MSG_PER_DAY,
    )


@router.post("/{agent_type}/cancel", response_model=AiSubscriptionInfo)
async def cancel_subscription(
    agent_type: AiAgentType,
    service: AiAgentService = Depends(get_ai_agent_service),
    user: UserRead = Depends(get_current_user),
) -> AiSubscriptionInfo:
    from app.services.ai_agent_service import AiAgentPolicy

    sub = await service.cancel_subscription(user.id, agent_type)
    return AiSubscriptionInfo(
        id=sub.id,
        status=sub.status.value,
        starts_at=sub.starts_at,
        expires_at=sub.expires_at,
        messages_today=sub.messages_today,
        max_messages_day=AiAgentPolicy.MAX_MSG_PER_DAY,
    )
