"""Substage 3C-2 — listing description mode tests."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.config import Settings
from app.core.exceptions import AppException
from app.models.listing_description_mode_enums import ListingDescriptionMode
from app.schemas.listing_description_mode import ListingDescriptionModeUpsertRequest
from app.services.listing_description_mode_service import ListingDescriptionModeService


def test_description_mode_flag_default_off() -> None:
    assert Settings().MEDIA_DESCRIPTION_MODE_ENABLED is False


@pytest.mark.asyncio
async def test_upsert_ai_assisted() -> None:
    settings = Settings(MEDIA_DESCRIPTION_MODE_ENABLED=True)
    session = MagicMock()
    session.flush = AsyncMock()
    listing = SimpleNamespace(id=1, owner_id=5, description_mode=None)
    svc = ListingDescriptionModeService(session, settings)
    svc._listings.get_by_id = AsyncMock(return_value=listing)

    result = await svc.upsert_mode(
        1,
        actor_user_id=5,
        payload=ListingDescriptionModeUpsertRequest(description_mode="ai_assisted"),
    )
    assert result.description_mode == "ai_assisted"
    assert listing.description_mode == ListingDescriptionMode.ai_assisted


@pytest.mark.asyncio
async def test_upsert_manual() -> None:
    settings = Settings(MEDIA_DESCRIPTION_MODE_ENABLED=True)
    session = MagicMock()
    session.flush = AsyncMock()
    listing = SimpleNamespace(id=1, owner_id=5, description_mode=None)
    svc = ListingDescriptionModeService(session, settings)
    svc._listings.get_by_id = AsyncMock(return_value=listing)

    result = await svc.upsert_mode(
        1,
        actor_user_id=5,
        payload=ListingDescriptionModeUpsertRequest(description_mode="manual"),
    )
    assert result.description_mode == "manual"


@pytest.mark.asyncio
async def test_upsert_rejected_when_flag_off() -> None:
    settings = Settings(MEDIA_DESCRIPTION_MODE_ENABLED=False)
    session = MagicMock()
    listing = SimpleNamespace(id=1, owner_id=5, description_mode=None)
    svc = ListingDescriptionModeService(session, settings)
    svc._listings.get_by_id = AsyncMock(return_value=listing)

    with pytest.raises(AppException) as exc:
        await svc.upsert_mode(
            1,
            actor_user_id=5,
            payload=ListingDescriptionModeUpsertRequest(description_mode="manual"),
        )
    assert exc.value.status_code == 404
