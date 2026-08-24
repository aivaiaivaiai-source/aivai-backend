from fastapi import APIRouter, Depends, File, Form, Request, UploadFile

from app.api.deps import get_current_user, get_direct_upload_service, get_media_service
from app.core.exceptions import AppException
from app.schemas.direct_upload import (
    DirectUploadCompleteResponse,
    DirectUploadInitiateRequest,
    DirectUploadInitiateResponse,
)
from app.schemas.media import MediaRead, MediaReorderRequest
from app.schemas.user import UserRead
from app.services.direct_upload_service import DirectUploadService
from app.services.media_service import MediaService
from app.services.storage_service import MAX_IMAGE_UPLOAD_BYTES, read_upload_limited

listings_media_router = APIRouter()
root_media_router = APIRouter()


async def _pair_uploads_with_client_ids(
    files: list[UploadFile],
    client_upload_ids: list[str] | None,
) -> list[tuple[bytes, str, str | None, str | None]]:
    if client_upload_ids is None:
        payloads: list[tuple[bytes, str, str | None, str | None]] = []
        for upload_file in files:
            content, content_type, source_name = await read_upload_limited(upload_file)
            payloads.append((content, content_type, source_name, None))
        return payloads

    if len(client_upload_ids) != len(files):
        raise AppException(
            "client_upload_ids length must match files length when provided.",
            status_code=400,
        )

    payloads = []
    for upload_file, client_id in zip(files, client_upload_ids, strict=True):
        content, content_type, source_name = await read_upload_limited(upload_file)
        normalized_id = client_id.strip() if client_id and client_id.strip() else None
        payloads.append((content, content_type, source_name, normalized_id))
    return payloads


@listings_media_router.post(
    "/{listing_id}/media/uploads",
    response_model=DirectUploadInitiateResponse,
    status_code=201,
)
async def initiate_direct_upload(
    listing_id: int,
    body: DirectUploadInitiateRequest,
    service: DirectUploadService = Depends(get_direct_upload_service),
    user: UserRead = Depends(get_current_user),
) -> DirectUploadInitiateResponse:
    return await service.initiate(listing_id, actor_user_id=user.id, body=body)


@listings_media_router.put(
    "/{listing_id}/media/{media_id}/upload",
    status_code=204,
)
async def direct_upload_put_bytes(
    listing_id: int,
    media_id: int,
    request: Request,
    service: DirectUploadService = Depends(get_direct_upload_service),
    user: UserRead = Depends(get_current_user),
) -> None:
    content_type = request.headers.get("content-type", "").split(";")[0].strip()
    if not content_type:
        raise AppException("Content-Type header is required.", status_code=400)
    body = await request.body()
    if len(body) > MAX_IMAGE_UPLOAD_BYTES:
        raise AppException("File too large; maximum size is 5 MB.", status_code=400)
    await service.put_upload_bytes(
        listing_id,
        media_id,
        actor_user_id=user.id,
        content=body,
        content_type=content_type,
    )


@listings_media_router.post(
    "/{listing_id}/media/{media_id}/complete",
    response_model=DirectUploadCompleteResponse,
)
async def complete_direct_upload(
    listing_id: int,
    media_id: int,
    service: DirectUploadService = Depends(get_direct_upload_service),
    user: UserRead = Depends(get_current_user),
) -> DirectUploadCompleteResponse:
    return await service.complete(listing_id, media_id, actor_user_id=user.id)


@listings_media_router.post(
    "/{listing_id}/media",
    response_model=list[MediaRead],
    status_code=201,
)
async def upload_listing_media(
    listing_id: int,
    files: list[UploadFile] = File(...),
    client_upload_ids: list[str] | None = Form(default=None),
    service: MediaService = Depends(get_media_service),
    user: UserRead = Depends(get_current_user),
) -> list[MediaRead]:
    payloads = await _pair_uploads_with_client_ids(files, client_upload_ids)
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
