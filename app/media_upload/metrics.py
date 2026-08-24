"""Stage 5 direct-upload metrics."""

from __future__ import annotations

import threading

_lock = threading.Lock()
_counters: dict[str, int] = {}


def incr(name: str, amount: int = 1) -> None:
    with _lock:
        _counters[name] = _counters.get(name, 0) + amount


def snapshot() -> dict[str, int]:
    with _lock:
        return dict(__counters)
