from fastapi import APIRouter

from app.api.v1.endpoints import (
    assistant,
    auth,
    categories,
    category_intelligence,
    chats,
    health,
    listings,
    media,
    notifications,
    saved_searches,
    users,
    vehicles,
    voice,
)

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(chats.router, prefix="/chats", tags=["chats"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(listings.router, prefix="/listings", tags=["listings"])
api_router.include_router(
    media.listings_media_router,
    prefix="/listings",
    tags=["media"],
)
api_router.include_router(
    media.root_media_router,
    prefix="/media",
    tags=["media"],
)
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])
api_router.include_router(vehicles.router, prefix="/vehicles", tags=["vehicles"])
api_router.include_router(
    category_intelligence.router,
    prefix="/categories/intelligence",
    tags=["category-intelligence"],
)
api_router.include_router(
    saved_searches.router,
    prefix="/saved-searches",
    tags=["saved-searches"],
)
api_router.include_router(
    notifications.router,
    prefix="/notifications",
    tags=["notifications"],
)
api_router.include_router(voice.router, prefix="/voice", tags=["voice"])
api_router.include_router(assistant.router, prefix="/assistant", tags=["assistant"])
