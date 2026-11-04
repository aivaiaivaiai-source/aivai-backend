# -*- coding: utf-8 -*-
"""Current USD→KGS rate — read for Flutter draft/Search; mutate is internal/dev."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.config import get_settings
from app.schemas.fx_rate import FxRateRead, FxRateUpdate
from app.services import fx_service

router = APIRouter()


@router.get("/usd-kgs", response_model=FxRateRead)
async def get_usd_kgs_rate(
    session: AsyncSession = Depends(get_db),
) -> FxRateRead:
    """Public read of current configured USD→KGS rate for draft Preview / Search UI."""
    row = await fx_service.get_current_usd_kgs_rate(session)
    return FxRateRead(
        pair=row.pair,
        rate=row.rate,
        source=row.source,
        rate_updated_at=row.rate_updated_at,
    )


@router.put("/usd-kgs", response_model=FxRateRead)
async def set_usd_kgs_rate(
    body: FxRateUpdate,
    session: AsyncSession = Depends(get_db),
    x_aivai_fx_admin_key: str | None = Header(default=None, alias="X-Aivai-Fx-Admin-Key"),
) -> FxRateRead:
    """Update current rate. Requires FX admin key — marketplace users cannot mutate."""
    expected = (get_settings().FX_RATE_ADMIN_KEY or "").strip()
    if not expected or not x_aivai_fx_admin_key or x_aivai_fx_admin_key != expected:
        raise HTTPException(status_code=403, detail="Forbidden")

    row = await fx_service.set_current_usd_kgs_rate(
        session,
        rate=body.rate,
        source=body.source or "configured",
    )
    await session.commit()
    return FxRateRead(
        pair=row.pair,
        rate=row.rate,
        source=row.source,
        rate_updated_at=row.rate_updated_at,
    )
