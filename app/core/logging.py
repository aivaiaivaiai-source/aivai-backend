from __future__ import annotations

import json
import logging
import os
import sys
from datetime import UTC, datetime
from typing import Any

from app.middleware.request_id import get_request_id


class _RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id() or "-"
        return True


class JsonLogFormatter(logging.Formatter):
    """Single-line JSON records for machine parsing."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "-"),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


class KeyValueLogFormatter(logging.Formatter):
    """Human-friendly structured line: key=value pairs."""

    _fmt = (
        "%(asctime)s %(levelname)s %(name)s "
        "request_id=%(request_id)s %(message)s"
    )

    def __init__(self) -> None:
        super().__init__(fmt=self._fmt, datefmt="%Y-%m-%dT%H:%M:%S%z")


def configure_logging() -> None:
    """Configure root + common library loggers once (idempotent)."""
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    use_json = os.getenv("LOG_JSON", "").lower() in {"1", "true", "yes"}

    root = logging.getLogger()
    if getattr(root, "_aivai_logging_configured", False):
        root.setLevel(level)
        return

    root.setLevel(level)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.addFilter(_RequestIdFilter())
    if use_json:
        handler.setFormatter(JsonLogFormatter())
    else:
        handler.setFormatter(KeyValueLogFormatter())

    root.handlers.clear()
    root.addHandler(handler)

    logging.getLogger("uvicorn.error").handlers = []
    logging.getLogger("uvicorn.error").propagate = True
    logging.getLogger("uvicorn.access").handlers = []
    logging.getLogger("uvicorn.access").propagate = True
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    setattr(root, "_aivai_logging_configured", True)
