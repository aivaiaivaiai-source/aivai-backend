from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user, get_notification_service
from app.core.constants import MAX_LIMIT
from app.schemas.notification import NotificationMarkReadRequest, NotificationRead
from app.schemas.user import UserRead
from app.services.notification_service import NotificationService

router = APIRouter()


@router.get("", response_model=list[NotificationRead])
async def list_notifications(
    service: NotificationService = Depends(get_notification_service),
    user: UserRead = Depends(get_current_user),
    limit: int = Query(default=100, ge=1, le=MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
) -> list[NotificationRead]:
    return await service.list_for_user(user.id, limit=limit, offset=offset)


@router.patch("/{notification_id}/read", response_model=NotificationRead)
async def mark_notification_read(
    notification_id: int,
    service: NotificationService = Depends(get_notification_service),
    user: UserRead = Depends(get_current_user),
) -> NotificationRead:
    return await service.mark_read(notification_id, user.id)


@router.post("/mark-read", response_model=dict)
async def mark_notifications_read(
    body: NotificationMarkReadRequest,
    service: NotificationService = Depends(get_notification_service),
    user: UserRead = Depends(get_current_user),
) -> dict[str, int]:
    n = await service.mark_read_many(user.id, body.ids)
    return {"updated": n}


@router.post("/read-all", response_model=dict)
async def mark_all_notifications_read(
    service: NotificationService = Depends(get_notification_service),
    user: UserRead = Depends(get_current_user),
) -> dict[str, int]:
    n = await service.mark_all_read(user.id)
    return {"updated": n}
