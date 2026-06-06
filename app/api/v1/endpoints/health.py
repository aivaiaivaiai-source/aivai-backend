from fastapi import APIRouter, Depends

from app.api.deps import get_health_service
from app.services.health_service import HealthService

router = APIRouter()


@router.get("", summary="Liveness + DB ping (SELECT 1)")
async def health(service: HealthService = Depends(get_health_service)) -> dict[str, str]:
    """Returns ``{"status": "ok"}`` after a successful database round-trip."""
    return await service.check()
