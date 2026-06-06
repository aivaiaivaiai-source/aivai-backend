from fastapi import APIRouter, Depends, Query, Response

from app.api.deps import get_current_user, get_saved_search_service
from app.core.constants import MAX_LIMIT
from app.schemas.saved_search import SavedSearchCreate, SavedSearchRead, SavedSearchUpdate
from app.schemas.user import UserRead
from app.services.saved_search_service import SavedSearchService

router = APIRouter()


@router.get("", response_model=list[SavedSearchRead])
async def list_saved_searches(
    service: SavedSearchService = Depends(get_saved_search_service),
    user: UserRead = Depends(get_current_user),
    limit: int = Query(default=100, ge=1, le=MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
) -> list[SavedSearchRead]:
    return await service.list_for_user(user.id, limit=limit, offset=offset)


@router.get("/{search_id}", response_model=SavedSearchRead)
async def get_saved_search(
    search_id: int,
    service: SavedSearchService = Depends(get_saved_search_service),
    user: UserRead = Depends(get_current_user),
) -> SavedSearchRead:
    return await service.get_for_user(search_id, user.id)


@router.post("", response_model=SavedSearchRead, status_code=201)
async def create_saved_search(
    body: SavedSearchCreate,
    service: SavedSearchService = Depends(get_saved_search_service),
    user: UserRead = Depends(get_current_user),
) -> SavedSearchRead:
    return await service.create_saved_search(body, user.id)


@router.patch("/{search_id}", response_model=SavedSearchRead)
async def update_saved_search(
    search_id: int,
    body: SavedSearchUpdate,
    service: SavedSearchService = Depends(get_saved_search_service),
    user: UserRead = Depends(get_current_user),
) -> SavedSearchRead:
    return await service.update_for_user(search_id, user.id, body)


@router.post("/{search_id}/toggle", response_model=SavedSearchRead)
async def toggle_saved_search(
    search_id: int,
    service: SavedSearchService = Depends(get_saved_search_service),
    user: UserRead = Depends(get_current_user),
) -> SavedSearchRead:
    return await service.toggle_for_user(search_id, user.id)


@router.delete("/{search_id}", status_code=204)
async def delete_saved_search(
    search_id: int,
    service: SavedSearchService = Depends(get_saved_search_service),
    user: UserRead = Depends(get_current_user),
) -> Response:
    await service.delete_for_user(search_id, user.id)
    return Response(status_code=204)
