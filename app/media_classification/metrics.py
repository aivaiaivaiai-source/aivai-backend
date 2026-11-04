"""Minimal classification metrics counters (in-process foundation)."""

from __future__ import annotations

from collections import defaultdict

_counters: dict[str, int] = defaultdict(int)


def incr(name: str, amount: int = 1) -> None:
    _counters[name] += amount


def get_counters() -> dict[str, int]:
    return dict(_counters)


def reset_counters() -> None:
    _counters.clear()
