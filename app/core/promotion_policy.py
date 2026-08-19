"""Single source of truth for listing promotion tariffs.

Keep this module free of I/O. Mobile mirrors the same numbers in
``promotion_policy.dart``. Ranking uses *tiers*, not exact som.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

from app.core.exceptions import AppException

DAILY_RATE_MIN = 70
DAILY_RATE_MAX = 150
DAYS_MIN = 1
DAYS_MAX = 30

# Inclusive bands. Higher tier ranks first among promoted listings.
# 70–89 → 1, 90–119 → 2, 120–150 → 3.
_TIER_BANDS: tuple[tuple[int, int, int], ...] = (
    (120, 150, 3),
    (90, 119, 2),
    (70, 89, 1),
)


@dataclass(frozen=True, slots=True)
class PromotionQuote:
    daily_rate: int
    days: int
    discount_percent: int
    subtotal: int
    discount: int
    total: int
    tier: int

    def window(self, *, starts_at: datetime) -> tuple[datetime, datetime]:
        ends_at = starts_at + timedelta(days=self.days)
        return starts_at, ends_at


def discount_percent(days: int) -> int:
    if days >= 20:
        return 30
    if days >= 10:
        return 20
    if days >= 2:
        return 10
    return 0


def tier_for_daily_rate(daily_rate: int) -> int:
    for low, high, tier in _TIER_BANDS:
        if low <= daily_rate <= high:
            return tier
    raise AppException(
        f"Daily rate must be between {DAILY_RATE_MIN} and {DAILY_RATE_MAX}",
        status_code=400,
        code="INVALID_PROMOTION_RATE",
    )


def quote(*, daily_rate: int, days: int) -> PromotionQuote:
    if daily_rate < DAILY_RATE_MIN or daily_rate > DAILY_RATE_MAX:
        raise AppException(
            f"Daily rate must be between {DAILY_RATE_MIN} and {DAILY_RATE_MAX}",
            status_code=400,
            code="INVALID_PROMOTION_RATE",
        )
    if days < DAYS_MIN or days > DAYS_MAX:
        raise AppException(
            f"Duration must be between {DAYS_MIN} and {DAYS_MAX} days",
            status_code=400,
            code="INVALID_PROMOTION_DAYS",
        )
    percent = discount_percent(days)
    subtotal = daily_rate * days
    discount = int(
        (Decimal(subtotal) * Decimal(percent) / Decimal(100)).quantize(
            Decimal("1"),
            rounding=ROUND_HALF_UP,
        )
    )
    return PromotionQuote(
        daily_rate=daily_rate,
        days=days,
        discount_percent=percent,
        subtotal=subtotal,
        discount=discount,
        total=subtotal - discount,
        tier=tier_for_daily_rate(daily_rate),
    )


def _as_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def is_active(*, is_promoted: bool, ends_at: datetime | None, now: datetime) -> bool:
    if not is_promoted or ends_at is None:
        return False
    return _as_utc(ends_at) > _as_utc(now)


def days_left(*, ends_at: datetime | None, now: datetime) -> int:
    if ends_at is None:
        return 0
    remaining = _as_utc(ends_at) - _as_utc(now)
    if remaining.total_seconds() <= 0:
        return 0
    return max(1, math.ceil(remaining.total_seconds() / 86400))


@dataclass(frozen=True, slots=True)
class StopRefund:
    charged_days: int
    refunded_days: int
    refund_amount: int


def _round_som(value: Decimal) -> int:
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def refund_on_stop(
    *,
    paid_total: int,
    purchased_days: int,
    starts_at: datetime,
    now: datetime,
) -> StopRefund:
    """Unused calendar days return to the wallet. The stop day is charged."""
    if purchased_days < 1 or paid_total <= 0:
        return StopRefund(charged_days=0, refunded_days=0, refund_amount=0)
    start_day = _as_utc(starts_at).date()
    today = _as_utc(now).date()
    elapsed = (today - start_day).days + 1
    charged = min(purchased_days, max(1, elapsed))
    refunded_days = purchased_days - charged
    amount = _round_som(
        Decimal(paid_total) * Decimal(refunded_days) / Decimal(purchased_days)
    )
    amount = max(0, min(amount, paid_total))
    return StopRefund(
        charged_days=charged,
        refunded_days=refunded_days,
        refund_amount=amount,
    )


def read_fields(row: object, *, now: datetime) -> dict[str, object]:
    """Effective promotion payload for API reads. Ignores a stale DB flag."""
    flag = bool(getattr(row, "is_promoted", False))
    ends_raw = getattr(row, "promotion_ends_at", None)
    starts_raw = getattr(row, "promotion_starts_at", None)
    ends_at = _as_utc(ends_raw) if isinstance(ends_raw, datetime) else None
    starts_at = _as_utc(starts_raw) if isinstance(starts_raw, datetime) else None
    active = is_active(is_promoted=flag, ends_at=ends_at, now=now)
    daily = getattr(row, "promotion_daily_rate", None)
    tier = int(getattr(row, "promotion_tier", 0) or 0)
    return {
        "is_promoted": active,
        "promotion_daily_rate": daily if active else None,
        "promotion_tier": tier if active else 0,
        "promotion_starts_at": starts_at if active else None,
        "promotion_ends_at": ends_at if active else None,
        "promotion_days_left": days_left(ends_at=ends_at, now=now) if active else 0,
    }
