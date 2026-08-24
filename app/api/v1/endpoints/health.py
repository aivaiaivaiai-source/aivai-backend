from fastapi import APIRouter, Depends

from app.api.deps import get_health_service
from app.core import ai_agent_metrics as metrics
from app.core.config import get_settings
from app.core.redis import redis_info
from app.media_queue import metrics as media_metrics
from app.media_engine import metrics as engine_metrics
from app.media_upload import metrics as upload_metrics
from app.media_queue.namespace import media_queue_prefix
from app.media_queue.streams import pending_summary, stream_length
from app.services.ai_match_queue import queue_depth
from app.services.health_service import HealthService

router = APIRouter()


@router.get("", summary="Liveness + DB ping (SELECT 1)")
async def health(service: HealthService = Depends(get_health_service)) -> dict[str, str]:
    """Returns ``{"status": "ok"}`` after a successful database round-trip."""
    return await service.check()


@router.get("/ai-agents", summary="AI agents queue/worker metrics")
async def ai_agents_health() -> dict:
    depth = await queue_depth()
    return {
        "status": "ok",
        "redis": await redis_info(),
        "metrics": metrics.snapshot(queue_depth=depth),
    }


@router.get("/media-queue", summary="Media Platform queue metrics (Stage 3)")
async def media_queue_health() -> dict:
    settings = get_settings()
    redis = await redis_info()
    depth = 0
    pending = {"pending": 0}
    if redis.get("available"):
        from app.core.redis import get_redis

        client = get_redis()
        if client is not None:
            depth = await stream_length(client, settings)
            pending = await pending_summary(client, settings)
    return {
        "status": "ok",
        "async_pipeline_enabled": settings.MEDIA_ASYNC_PIPELINE_ENABLED,
        "direct_upload_enabled": settings.MEDIA_DIRECT_UPLOAD_ENABLED,
        "cdn_configured": bool(settings.MEDIA_CDN_BASE_URL),
        "storage_backend": settings.MEDIA_STORAGE_BACKEND,
        "namespace": media_queue_prefix(settings),
        "redis": redis,
        "queue_depth": depth,
        "pending": pending,
        "metrics": media_metrics.snapshot(queue_depth=depth),
        "engine_metrics": engine_metrics.snapshot(),
        "upload_metrics": upload_metrics.snapshot(),
        "worker_replicas": {
            "min": settings.MEDIA_WORKER_MIN_REPLICAS,
            "max": settings.MEDIA_WORKER_MAX_REPLICAS,
        },
    }
