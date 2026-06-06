from __future__ import annotations

import uuid
from contextvars import ContextVar, Token

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

_REQUEST_ID_CTX: ContextVar[str] = ContextVar("request_id", default="")


def get_request_id() -> str:
    return _REQUEST_ID_CTX.get() or ""


def set_request_id(value: str) -> Token[str]:
    return _REQUEST_ID_CTX.set(value)


def reset_request_id(token: Token[str]) -> None:
    _REQUEST_ID_CTX.reset(token)


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Assigns or propagates ``X-Request-ID`` and stores it in a logging context var."""

    header_name = "X-Request-ID"

    async def dispatch(self, request: Request, call_next) -> Response:
        raw = request.headers.get(self.header_name.lower())
        rid = raw.strip() if raw and raw.strip() else str(uuid.uuid4())
        token = set_request_id(rid)
        try:
            response = await call_next(request)
            response.headers[self.header_name] = rid
            return response
        finally:
            reset_request_id(token)
