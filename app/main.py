from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import SQLAlchemyError

from app.api.deps import get_health_service
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions import AppException
from app.core.logging import configure_logging
from app.middleware.request_id import get_request_id
from app.middleware.request_id import RequestIdMiddleware
from app.core.redis import close_redis, init_redis
from app.services.ai_match_worker import ai_maintenance_loop, ai_match_worker_loop
from app.services.ai_realtime_hub import start_redis_pubsub_bridge
from app.services.assistant_conversation_cleanup_worker import (
    assistant_conversation_cleanup_loop,
)
from app.services.health_service import HealthService


logger = logging.getLogger(__name__)


def _error_body(
    *,
    detail: str,
    code: str,
    status: int,
    extra: dict[str, object] | None = None,
) -> dict[str, object]:
    body: dict[str, object] = {
        "detail": detail,
        "code": code,
        "status": status,
        "request_id": get_request_id() or "",
    }
    if extra:
        body.update(extra)
    return body


def _json_error(
    *,
    detail: str,
    code: str,
    status: int,
    extra: dict[str, object] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content=_error_body(detail=detail, code=code, status=status, extra=extra),
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    key = _settings.OPENAI_API_KEY
    whisper_ready = bool(key and key.strip())
    logger.info(
        "whisper_stt_configured=%s env_file=%s",
        whisper_ready,
        "present" if whisper_ready else "missing OPENAI_API_KEY",
    )
    await init_redis()
    stop_cleanup = asyncio.Event()
    stop_ai = asyncio.Event()
    cleanup_task = asyncio.create_task(
        assistant_conversation_cleanup_loop(
            settings=_settings,
            stop_event=stop_cleanup,
        ),
        name="assistant_conversation_cleanup",
    )
    ai_match_task = asyncio.create_task(
        ai_match_worker_loop(stop_event=stop_ai),
        name="ai_match_worker",
    )
    ai_maintenance_task = asyncio.create_task(
        ai_maintenance_loop(settings=_settings, stop_event=stop_ai),
        name="ai_maintenance",
    )
    ai_pubsub_task = asyncio.create_task(
        start_redis_pubsub_bridge(stop_ai),
        name="ai_realtime_pubsub",
    )
    logger.info("Application startup complete.")
    try:
        yield
    finally:
        stop_cleanup.set()
        stop_ai.set()
        for task in (cleanup_task, ai_match_task, ai_maintenance_task, ai_pubsub_task):
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        await close_redis()


_settings = get_settings()


def create_app() -> FastAPI:
    application = FastAPI(
        title="AiVai API",
        version="0.1.0",
        lifespan=lifespan,
    )

    from app.storage.factory import should_mount_static_media

    if should_mount_static_media(_settings):
        _media_dir = Path(_settings.MEDIA_ROOT).resolve()
        _media_dir.mkdir(parents=True, exist_ok=True)
        _mount = "/" + _settings.MEDIA_URL.strip("/")
        application.mount(_mount, StaticFiles(directory=str(_media_dir)), name="media")
    else:
        # S3/R2: media is not served via FastAPI StaticFiles.
        Path(_settings.MEDIA_ROOT).mkdir(parents=True, exist_ok=True)

    application.add_middleware(RequestIdMiddleware)

    @application.exception_handler(AppException)
    async def app_exception_handler(
        _request: Request,
        exc: AppException,
    ) -> JSONResponse:
        return _json_error(
            detail=exc.message or exc.__class__.__name__,
            code=exc.error_code,
            status=exc.status_code,
            extra=exc.extra or None,
        )

    @application.exception_handler(SQLAlchemyError)
    async def sqlalchemy_exception_handler(
        _request: Request,
        _exc: SQLAlchemyError,
    ) -> JSONResponse:
        logger.error("sqlalchemy_error", exc_info=_exc)
        return _json_error(
            detail="A database error occurred.",
            code="DATABASE_ERROR",
            status=500,
        )

    @application.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        _request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        parts: list[str] = []
        for err in exc.errors()[:8]:
            loc = err.get("loc") or ()
            loc_txt = ".".join(str(x) for x in loc if x != "body")
            msg = err.get("msg", "invalid")
            if loc_txt:
                parts.append(f"{loc_txt}: {msg}")
            else:
                parts.append(str(msg))
        detail = "; ".join(parts) if parts else "Request validation failed."
        return _json_error(
            detail=detail,
            code="VALIDATION_ERROR",
            status=422,
        )

    @application.get("/ready")
    async def ready(
        service: HealthService = Depends(get_health_service),
    ) -> dict[str, str]:
        return await service.check()

    application.include_router(api_router, prefix="/api/v1")
    return application


app = create_app()
