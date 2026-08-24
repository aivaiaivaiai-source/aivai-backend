"""Media Engine instrumentation (Stage 4)."""

from __future__ import annotations

import threading
import time
from contextlib import contextmanager
from typing import Iterator

_lock = threading.Lock()
_counters: dict[str, int] = {}
_durations_ms: dict[str, float] = {}


def incr(name: str, amount: int = 1) -> None:
    with _lock:
        _counters[name] = _counters.get(name, 0) + amount


def add_duration(name: str, ms: float) -> None:
    with _lock:
        _durations_ms[name] = _durations_ms.get(name, 0.0) + ms


def add_bytes(name: str, nbytes: int) -> None:
    incr(name, max(0, nbytes))


@contextmanager
def timed(name: str) -> Iterator[None]:
    start = time.perf_counter()
    try:
        yield
    finally:
        add_duration(name, (time.perf_counter() - start) * 1000.0)


def snapshot() -> dict[str, float | int]:
    with _lock:
        data: dict[str, float | int] = dict(_counters)
        data.update(_durations_ms)
    return data
