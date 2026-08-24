"""In-process counters for media worker autoscaling signals."""

from __future__ import annotations

import threading
from typing import Any

_lock = threading.Lock()
_counters: dict[str, int] = {}


def incr(name: str, amount: int = 1) -> None:
    with _lock:
        _counters[name] = _counters.get(name, 0) + amount


def set_gauge(name: str, value: int) -> None:
    with _lock:
        _counters[name] = value


def snapshot(*, queue_depth: int | None = None) -> dict[str, Any]:
    with _lock:
        data = dict(_counters)
    if queue_depth is not None:
        data["queue_depth"] = queue_depth
    return data
