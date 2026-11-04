"""Apply / validate listing.vehicle_execution against model allowed executions."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AppException
from app.models.category_enums import VehicleExecution
from app.models.enums import ListingStatus
from app.models.listing import Listing
from app.models.listing_field_value import ListingFieldValue
from app.models.vehicle import VehicleModel
from app.services.vehicle_execution import EXECUTION_PLACEMENT_SLUG

_CAR_SALE_SLUG = "transport-car-sale"


async def _model_allowed(session: AsyncSession, model_id: int) -> list[VehicleExecution]:
    stmt = (
        select(VehicleModel)
        .where(VehicleModel.id == model_id)
        .options(selectinload(VehicleModel.allowed_executions))
    )
    row = (await session.execute(stmt)).scalar_one_or_none()
    if row is None:
        return []
    return [e.execution for e in (row.allowed_executions or [])]


async def listing_model_id(session: AsyncSession, listing_id: int) -> int | None:
    stmt = (
        select(ListingFieldValue.ref_model_id)
        .where(
            ListingFieldValue.listing_id == listing_id,
            ListingFieldValue.field_key == "model",
            ListingFieldValue.ref_model_id.is_not(None),
        )
        .limit(1)
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def apply_listing_vehicle_execution(
    session: AsyncSession,
    listing: Listing,
    *,
    requested: VehicleExecution | None,
    category_slug: str | None,
    status: ListingStatus,
) -> VehicleExecution | None:
    """
    Normalize listing.vehicle_execution.

    - Models without a policy: execution stays None (ignore requested).
    - Cargo-only: auto cargo when omitted.
    - Dual: require explicit choice when publishing active; drafts may defer.
    - Car-sale must not accept models that have an execution policy.
    """
    model_id = await listing_model_id(session, listing.id)
    if model_id is None:
        listing.vehicle_execution = None
        return None

    allowed = await _model_allowed(session, model_id)
    if not allowed:
        if requested is not None:
            # No policy → free-text/legacy passenger-car models.
            listing.vehicle_execution = None
        return listing.vehicle_execution

    if category_slug == _CAR_SALE_SLUG:
        raise AppException(
            "This model is not available for passenger-car sale publication",
            status_code=400,
            code="VEHICLE_MODEL_NOT_FOR_CAR_SALE",
        )

    chosen = requested
    if chosen is None and len(allowed) == 1:
        chosen = allowed[0]
    if chosen is None:
        if status == ListingStatus.active:
            raise AppException(
                "vehicle_execution is required for this model",
                status_code=400,
                code="VEHICLE_EXECUTION_REQUIRED",
            )
        listing.vehicle_execution = None
        return None

    if chosen not in allowed:
        raise AppException(
            f"vehicle_execution '{chosen.value}' is not allowed for this model",
            status_code=400,
            code="VEHICLE_EXECUTION_NOT_ALLOWED",
        )

    listing.vehicle_execution = chosen
    return chosen


def placement_slug_for_execution(execution: VehicleExecution | None) -> str | None:
    if execution is None:
        return None
    return EXECUTION_PLACEMENT_SLUG.get(execution)
