from fastapi import APIRouter, Depends, File, Query, UploadFile

from app.api.deps import get_current_user, get_review_service, get_user_service
from app.core.constants import MAX_LIMIT
from app.schemas.review import ReviewCreate, ReviewRead, ReviewReplyUpdate
from app.schemas.user import UserByPhoneRequest, UserRead, UserUpdate
from app.schemas.wallet import WalletTopup
from app.services.storage_service import read_upload_limited
from app.services.user_service import ReviewService, UserService

router = APIRouter()


@router.get("/me", response_model=UserRead)
async def read_me(
    current: UserRead = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> UserRead:
    return await service.get_profile(current.id)


@router.patch("/me", response_model=UserRead)
async def patch_me(
    body: UserUpdate,
    current: UserRead = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> UserRead:
    return await service.update_me(current.id, body)


@router.post("/me/avatar", response_model=UserRead)
async def upload_my_avatar(
    file: UploadFile = File(...),
    current: UserRead = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> UserRead:
    content, content_type, _name = await read_upload_limited(file)
    return await service.upload_avatar(
        current.id,
        content=content,
        content_type=content_type,
    )


@router.post("/me/wallet/topup", response_model=UserRead)
async def topup_my_wallet(
    body: WalletTopup,
    current: UserRead = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> UserRead:
    """Placeholder credit until a payment provider is wired."""
    return await service.topup_wallet(current.id, body.amount)


@router.post("/by-phone", response_model=UserRead)
async def get_or_create_user_by_phone(
    body: UserByPhoneRequest,
    service: UserService = Depends(get_user_service),
) -> UserRead:
    return await service.get_or_create_user_by_phone(body.phone, body.full_name)


@router.get("", response_model=list[UserRead])
async def list_users(
    service: UserService = Depends(get_user_service),
    limit: int = Query(default=100, ge=1, le=MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
) -> list[UserRead]:
    return await service.list_users(limit=limit, offset=offset)


@router.get("/{user_id}", response_model=UserRead)
async def read_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
) -> UserRead:
    return await service.get_profile(user_id)


@router.get("/{user_id}/reviews", response_model=list[ReviewRead])
async def list_user_reviews(
    user_id: int,
    service: ReviewService = Depends(get_review_service),
    limit: int = Query(default=40, ge=1, le=MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
) -> list[ReviewRead]:
    return await service.list_for_user(user_id, limit=limit, offset=offset)


@router.post("/{user_id}/reviews", response_model=ReviewRead, status_code=201)
async def create_user_review(
    user_id: int,
    body: ReviewCreate,
    service: ReviewService = Depends(get_review_service),
    user: UserRead = Depends(get_current_user),
) -> ReviewRead:
    return await service.create_review(
        user_id,
        author_id=user.id,
        rating=body.rating,
        comment=body.comment,
    )


@router.patch("/{user_id}/reviews/{review_id}", response_model=ReviewRead)
async def reply_to_review(
    user_id: int,
    review_id: int,
    body: ReviewReplyUpdate,
    service: ReviewService = Depends(get_review_service),
    user: UserRead = Depends(get_current_user),
) -> ReviewRead:
    return await service.reply(
        review_id,
        current_user_id=user.id,
        owner_reply=body.owner_reply,
    )
