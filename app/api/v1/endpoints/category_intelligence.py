from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_category_intelligence_service
from app.schemas.category_intelligence import (
    CategoryDialogueRequest,
    CategoryDialogueResponse,
    CategoryIntelligenceRead,
    CategoryRoutingResult,
    TextRequest,
    VehicleResolveResult,
)
from app.services.category_intelligence_service import CategoryIntelligenceService

router = APIRouter()


@router.post("/route", response_model=CategoryRoutingResult)
async def route_intent(
    payload: TextRequest,
    service: CategoryIntelligenceService = Depends(get_category_intelligence_service),
) -> CategoryRoutingResult:
    """Map free-form user text to marketplace category (AI routing layer)."""
    return await service.route_intent(payload.text)


@router.post("/dialogue", response_model=CategoryDialogueResponse)
async def ai_dialogue(
    payload: CategoryDialogueRequest,
    service: CategoryIntelligenceService = Depends(get_category_intelligence_service),
) -> CategoryDialogueResponse:
    """AI assistant dialogue: route + ask only missing CORE fields."""
    return await service.dialogue(payload)


@router.post("/vehicle/resolve", response_model=VehicleResolveResult)
async def resolve_vehicle(
    payload: TextRequest,
    service: CategoryIntelligenceService = Depends(get_category_intelligence_service),
) -> VehicleResolveResult:
    """Resolve colloquial vehicle names to brand/model."""
    return await service.resolve_vehicle(payload.text)


@router.get("/{category_id}", response_model=CategoryIntelligenceRead)
async def get_category_intelligence(
    category_id: int,
    service: CategoryIntelligenceService = Depends(get_category_intelligence_service),
) -> CategoryIntelligenceRead:
    row = await service.get_category_intelligence(category_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return row
