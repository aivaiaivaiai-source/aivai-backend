from fastapi import APIRouter, Depends, File, UploadFile

from app.api.deps import get_current_user, get_media_service
from app.schemas.media import MediaRead, MediaReorderRequest
from app.schemas.user import UserRead
from app.services.media_service import MediaService
from app.services.storage_service import read_upload_limited

listings_media_router = APIRouter()
root_media_router = APIRouter()


@listings_media_router.post(
    "/{listing_id}/media",
    response_model=list[MediaRead],
    status_code=201,
)
async def upload_listing_media(
    listing_id: int,
    files: list[UploadFile] = File(...),
    service: MediaService = Depends(get_media_service),
    user: UserRead = Depends(get_current_user),
) -> list[MediaRead]:
    payloads = [await read_upload_limited(f) for f in files]
    return await service.add_images(
        listing_id,
        actor_user_id=user.id,
        payloads=payloads,
    )


@root_media_router.delete("/{image_id}", status_code=204)
async def delete_media(
    image_id: int,
    service: MediaService = Depends(get_media_service),
    user: UserRead = Depends(get_current_user),
) -> None:
    await service.delete_image(image_id, actor_user_id=user.id)


@listings_media_router.patch(
    "/{listing_id}/media/order",
    response_model=list[MediaRead],
)
async def reorder_listing_media(
    listing_id: int,
    body: MediaReorderRequest,
    service: MediaService = Depends(get_media_service),
    user: UserRead = Depends(get_current_user),
) -> list[MediaRead]:
    return await service.reorder_images(
        listing_id,
        actor_user_id=user.id,
        body=body,
    )
