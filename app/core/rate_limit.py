from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

from fastapi import Request

from app.core.constants import LISTING_CREATE_MAX_REQUESTS, LISTING_CREATE_WINDOW_SECONDS
from app.core.exceptions import RateLimitExceededError


class InMemoryRateLimiter:
    """Fixed sliding window using monotonic timestamps (per-process memory only)."""

    def __init__(self, *, max_requests: int, window_seconds: float) -> None:
        if max_requests < 1:
            raise ValueError("max_requests must be >= 1")
        if window_seconds <= 0:
            raise ValueError("window_seconds must be > 0")
        self._max = max_requests
        self._window = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    async def hit(self, key: str) -> None:
        """Record one hit or raise ``RateLimitExceededError``."""
        now = time.monotonic()
        cutoff = now - self._window
        with self._lock:
            bucket = self._hits[key]
            while bucket and bucket[0] < cutoff:
                bucket.popleft()
            if len(bucket) >= self._max:
                raise RateLimitExceededError(
                    "Too many requests. Please try again later.",
                )
            bucket.append(now)

    async def reset(self) -> None:
        with self._lock:
            self._hits.clear()


AUTH_IP_LIMITER = InMemoryRateLimiter(max_requests=5, window_seconds=60.0)
LISTING_CREATE_LIMITER = InMemoryRateLimiter(
    max_requests=LISTING_CREATE_MAX_REQUESTS,
    window_seconds=LISTING_CREATE_WINDOW_SECONDS,
)


async def enforce_auth_ip_rate_limit(request: Request) -> None:
    """Limit POST ``/auth/login`` and ``/auth/refresh`` by client IP."""
    client = request.client
    ip = client.host if client else "unknown"
    await AUTH_IP_LIMITER.hit(f"auth:{ip}")
