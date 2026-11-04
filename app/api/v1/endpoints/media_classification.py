"""Listing media classification endpoints (Substage 2)."""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.config import get_settings
from app.db.session import async_session_maker
from app.schemas.media_classification import (
    MediaClassificationConfirmRequest,
    MediaClassificationConfirmResponse,
    MediaClassificationRead,
)
from app.schemas.user import UserRead
from app.services.media_classification_service import MediaClassificationService

router = APIRouter()


async def _background_process(classification_id: int) -> None:
    settings = get_settings()
    async with async_session_maker() as session:
        svc = MediaClassificationService(session, settings)
        await svc.process_job(classification_id)
        await session.commit()


@router.get(
    "/{listing_id}/media-classification",
    response_model=MediaClassificationRead,
)
async def get_media_classification(
    listing_id: int,
    user: UserRead = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> MediaClassificationRead:
    svc = MediaClassificationService(session, get_settings())
    return await svc.get_status(listing_id, actor_user_id=user.id)


@router.post(
    "/{listing_id}/media-classification/ensure",
    response_model=MediaClassificationRead,
)
async def ensure_media_classification(
    listing_id: int,
    background_tasks: BackgroundTasks,
    user: UserRead = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> MediaClassificationRead:
    """Enqueue classification for current media set; process async (non-blocking)."""
    settings = get_settings()
    svc = MediaClassificationService(session, settings)
    row = await svc.ensure_job_for_listing(listing_id, actor_user_id=user.id)
    await session.commit()
    if row is not None and row.status.value == "pending":
        background_tasks.add_task(_background_process, row.id)
    return await svc.get_status(listing_id, actor_user_id=user.id)


@router.post(
    "/{listing_id}/media-classification/confirm",
    response_model=MediaClassificationConfirmResponse,
)
async def confirm_media_classification(
    listing_id: int,
    body: MediaClassificationConfirmRequest,
    user: UserRead = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> MediaClassificationConfirmResponse:
    svc = MediaClassificationService(session, get_settings())
    return await svc.confirm_category(
        listing_id,
        actor_user_id=user.id,
        category_id=body.category_id,
        classification_id=body.classification_id,
    )
