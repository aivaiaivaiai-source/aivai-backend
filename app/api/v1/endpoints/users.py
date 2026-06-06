from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user, get_user_service
from app.core.constants import MAX_LIMIT
from app.schemas.user import UserByPhoneRequest, UserRead
from app.services.user_service import UserService

router = APIRouter()


@router.get("/me", response_model=UserRead)
async def read_me(current: UserRead = Depends(get_current_user)) -> UserRead:
    return current


@router.get("", response_model=list[UserRead])
async def list_users(
    service: UserService = Depends(get_user_service),
    limit: int = Query(default=100, ge=1, le=MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
) -> list[UserRead]:
    return await service.list_users(limit=limit, offset=offset)


@router.post("/by-phone", response_model=UserRead)
async def get_or_create_user_by_phone(
    body: UserByPhoneRequest,
    service: UserService = Depends(get_user_service),
) -> UserRead:
    return await service.get_or_create_user_by_phone(body.phone, body.full_name)
