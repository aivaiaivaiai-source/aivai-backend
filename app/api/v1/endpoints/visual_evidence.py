"""Listing visual evidence endpoints (Substage 3C-2)."""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.config import get_settings
from app.db.session import async_session_maker
from app.schemas.user import UserRead
from app.schemas.visual_evidence import VisualEvidenceRead
from app.services.visual_evidence_service import VisualEvidenceService

router = APIRouter()


async def _background_process(evidence_id: int) -> None:
    settings = get_settings()
    async with async_session_maker() as session:
        svc = VisualEvidenceService(session, settings)
        await svc.process_job(evidence_id)
        await session.commit()


@router.get(
    "/{listing_id}/visual-evidence",
    response_model=VisualEvidenceRead,
)
async def get_visual_evidence(
    listing_id: int,
    user: UserRead = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> VisualEvidenceRead:
    svc = VisualEvidenceService(session, get_settings())
    return await svc.get_status(listing_id, actor_user_id=user.id)


@router.post(
    "/{listing_id}/visual-evidence/ensure",
    response_model=VisualEvidenceRead,
)
async def ensure_visual_evidence(
    listing_id: int,
    background_tasks: BackgroundTasks,
    user: UserRead = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> VisualEvidenceRead:
    """Idempotent enqueue for current media fingerprint; worker/background processes."""
    settings = get_settings()
    svc = VisualEvidenceService(session, settings)
    row = await svc.ensure_job_for_listing(listing_id, actor_user_id=user.id)
    await session.commit()
    if row is not None and row.status.value == "pending":
        background_tasks.add_task(_background_process, row.id)
    return await svc.get_status(listing_id, actor_user_id=user.id)
