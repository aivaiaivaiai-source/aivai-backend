from datetime import UTC, datetime, timedelta

import pytest

from app.core.exceptions import AppException
from app.core.promotion_policy import (
    days_left,
    is_active,
    quote,
    read_fields,
    refund_on_stop,
    tier_for_daily_rate,
)


def test_tiers_band_same_rank_inside_bucket() -> None:
    assert tier_for_daily_rate(70) == 1
    assert tier_for_daily_rate(75) == 1
    assert tier_for_daily_rate(89) == 1
    assert tier_for_daily_rate(90) == 2
    assert tier_for_daily_rate(119) == 2
    assert tier_for_daily_rate(120) == 3
    assert tier_for_daily_rate(150) == 3


def test_quote_discounts_match_ui() -> None:
    one = quote(daily_rate=70, days=1)
    assert one.discount_percent == 0
    assert one.total == 70
    assert one.tier == 1

    week = quote(daily_rate=70, days=7)
    assert week.discount_percent == 10
    assert week.subtotal == 490
    assert week.discount == 49
    assert week.total == 441

    mid = quote(daily_rate=75, days=7)
    assert mid.tier == 1
    assert mid.discount == 53  # 52.5 rounded half-up
    assert mid.total == 472

    ten = quote(daily_rate=90, days=10)
    assert ten.discount_percent == 20
    assert ten.tier == 2
    assert ten.total == 720

    month = quote(daily_rate=150, days=30)
    assert month.discount_percent == 30
    assert month.tier == 3
    assert month.total == 3150


def test_quote_rejects_out_of_range() -> None:
    with pytest.raises(AppException) as low:
        quote(daily_rate=69, days=1)
    assert low.value.code == "INVALID_PROMOTION_RATE"
    with pytest.raises(AppException) as days:
        quote(daily_rate=70, days=31)
    assert days.value.code == "INVALID_PROMOTION_DAYS"


def test_is_active_and_days_left() -> None:
    now = datetime(2026, 8, 18, 12, 0, tzinfo=UTC)
    assert is_active(is_promoted=True, ends_at=None, now=now) is False
    assert is_active(is_promoted=False, ends_at=now + timedelta(days=1), now=now) is False
    ends = now + timedelta(hours=1)
    assert is_active(is_promoted=True, ends_at=ends, now=now) is True
    assert days_left(ends_at=ends, now=now) == 1
    assert days_left(ends_at=now, now=now) == 0


def test_refund_on_stop_keeps_today_returns_rest() -> None:
    start = datetime(2026, 8, 18, 10, 0, tzinfo=UTC)
    week = quote(daily_rate=70, days=7)
    same_day = refund_on_stop(
        paid_total=week.total,
        purchased_days=7,
        starts_at=start,
        now=start + timedelta(hours=3),
    )
    assert same_day.charged_days == 1
    assert same_day.refunded_days == 6
    assert same_day.refund_amount == 378  # 441 * 6 / 7

    next_day = refund_on_stop(
        paid_total=week.total,
        purchased_days=7,
        starts_at=start,
        now=datetime(2026, 8, 19, 9, 0, tzinfo=UTC),
    )
    assert next_day.charged_days == 2
    assert next_day.refunded_days == 5
    assert next_day.refund_amount == 315

    last_day = refund_on_stop(
        paid_total=week.total,
        purchased_days=7,
        starts_at=start,
        now=datetime(2026, 8, 24, 12, 0, tzinfo=UTC),
    )
    assert last_day.charged_days == 7
    assert last_day.refunded_days == 0
    assert last_day.refund_amount == 0

    one_day = refund_on_stop(
        paid_total=70,
        purchased_days=1,
        starts_at=start,
        now=start + timedelta(hours=2),
    )
    assert one_day.charged_days == 1
    assert one_day.refund_amount == 0


def test_read_fields_ignores_stale_flag() -> None:
    now = datetime(2026, 8, 18, tzinfo=UTC)

    class Row:
        is_promoted = True
        promotion_daily_rate = 90
        promotion_tier = 2
        promotion_starts_at = now - timedelta(days=10)
        promotion_ends_at = now - timedelta(seconds=1)

    fields = read_fields(Row(), now=now)
    assert fields["is_promoted"] is False
    assert fields["promotion_tier"] == 0
    assert fields["promotion_days_left"] == 0
    assert fields["promotion_daily_rate"] is None
