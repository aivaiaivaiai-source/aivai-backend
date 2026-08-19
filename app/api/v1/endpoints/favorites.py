from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user, get_favorite_service
from app.core.constants import MAX_LIMIT
from app.schemas.favorite import FavoriteToggleRead
from app.schemas.listing import ListingFeedPage
from app.schemas.user import UserRead
from app.services.favorite_service import FavoriteService

router = APIRouter()


@router.get("", response_model=ListingFeedPage)
async def list_favorites(
    service: FavoriteService = Depends(get_favorite_service),
    user: UserRead = Depends(get_current_user),
    limit: int = Query(default=40, ge=1, le=MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
) -> ListingFeedPage:
    return await service.list_for_user(user.id, limit=limit, offset=offset)


@router.post("/{listing_id}/toggle", response_model=FavoriteToggleRead)
async def toggle_favorite(
    listing_id: int,
    service: FavoriteService = Depends(get_favorite_service),
    user: UserRead = Depends(get_current_user),
) -> FavoriteToggleRead:
    return await service.toggle(user.id, listing_id)
