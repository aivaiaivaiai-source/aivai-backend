"""In-process + optional Redis-backed counters for AI agents ops."""

from __future__ import annotations

import threading
import time
from typing import Any

_lock = threading.Lock()
_counters: dict[str, float] = {
    "enqueue_total": 0,
    "enqueue_deduped": 0,
    "dequeue_total": 0,
    "match_ok_total": 0,
    "match_error_total": 0,
    "match_latency_ms_sum": 0,
    "match_latency_ms_count": 0,
    "expired_subscriptions_total": 0,
    "ws_connect_total": 0,
    "ws_publish_total": 0,
}
_started_at = time.time()


def incr(name: str, amount: float = 1) -> None:
    with _lock:
        _counters[name] = _counters.get(name, 0) + amount


def observe_match_latency_ms(ms: float) -> None:
    with _lock:
        _counters["match_latency_ms_sum"] = _counters.get("match_latency_ms_sum", 0) + ms
        _counters["match_latency_ms_count"] = _counters.get("match_latency_ms_count", 0) + 1


def snapshot(*, queue_depth: int | None = None) -> dict[str, Any]:
    with _lock:
        data = dict(_counters)
    count = data.get("match_latency_ms_count", 0) or 0
    avg = (data.get("match_latency_ms_sum", 0) / count) if count else 0.0
    out: dict[str, Any] = {
        **data,
        "match_latency_ms_avg": round(avg, 2),
        "uptime_seconds": round(time.time() - _started_at, 1),
    }
    if queue_depth is not None:
        out["queue_depth"] = queue_depth
    return out
