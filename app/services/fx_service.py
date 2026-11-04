# -*- coding: utf-8 -*-
"""Trusted USD→KGS rate + listing snapshot/normalized helpers."""
from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.models.enums import Currency
from app.models.fx_rate import FX_PAIR_USD_KGS, FxRate
from app.models.listing import Listing

# Dev/migration seed only — never used by Flutter as live SoT.
CONFIGURED_FALLBACK_RATE = Decimal("89")
RATE_QUANT = Decimal("0.000001")
NORMALIZED_QUANT = Decimal("0.01")


def quantize_rate(rate: Decimal) -> Decimal:
    return rate.quantize(RATE_QUANT)


def quantize_money(amount: Decimal) -> Decimal:
    return amount.quantize(NORMALIZED_QUANT, rounding=ROUND_HALF_UP)


def validate_rate(rate: Decimal | float | int | str) -> Decimal:
    value = Decimal(str(rate))
    if value <= 0:
        raise AppException("FX rate must be positive.", status_code=400)
    if value > Decimal("1000000"):
        raise AppException("FX rate is unreasonably large.", status_code=400)
    return quantize_rate(value)


def compute_normalized_price_kgs(
    *,
    price: Decimal,
    currency: Currency | str,
    snapshot: Decimal,
) -> Decimal:
    cur = currency if isinstance(currency, Currency) else Currency(str(currency))
    rate = validate_rate(snapshot)
    amount = Decimal(str(price))
    if cur == Currency.KGS:
        return quantize_money(amount)
    if cur == Currency.USD:
        return quantize_money(amount * rate)
    raise AppException(f"Unsupported currency: {cur}", status_code=400)


async def get_current_usd_kgs_rate(session: AsyncSession) -> FxRate:
    row = (
        await session.execute(
            select(FxRate).where(FxRate.pair == FX_PAIR_USD_KGS).limit(1)
        )
    ).scalar_one_or_none()
    if row is None:
        raise AppException(
            "Не удалось определить курс валют. Попробуйте опубликовать немного позже.",
            status_code=503,
        )
    validate_rate(row.rate)
    return row


async def ensure_fx_rate_row(
    session: AsyncSession,
    *,
    rate: Decimal = CONFIGURED_FALLBACK_RATE,
    source: str = "configured",
) -> FxRate:
    existing = (
        await session.execute(
            select(FxRate).where(FxRate.pair == FX_PAIR_USD_KGS).limit(1)
        )
    ).scalar_one_or_none()
    if existing is not None:
        return existing
    row = FxRate(
        pair=FX_PAIR_USD_KGS,
        rate=validate_rate(rate),
        source=source,
        rate_updated_at=datetime.now(UTC),
    )
    session.add(row)
    await session.flush()
    return row


async def set_current_usd_kgs_rate(
    session: AsyncSession,
    *,
    rate: Decimal | float | int | str,
    source: str = "configured",
) -> FxRate:
    value = validate_rate(rate)
    row = (
        await session.execute(
            select(FxRate).where(FxRate.pair == FX_PAIR_USD_KGS).limit(1)
        )
    ).scalar_one_or_none()
    now = datetime.now(UTC)
    if row is None:
        row = FxRate(
            pair=FX_PAIR_USD_KGS,
            rate=value,
            source=source,
            rate_updated_at=now,
        )
        session.add(row)
    else:
        row.rate = value
        row.source = source
        row.rate_updated_at = now
    await session.flush()
    return row


def apply_listing_fx_snapshot(
    listing: Listing,
    *,
    rate: Decimal,
) -> None:
    """Set snapshot + normalized from trusted rate (publication / price edit)."""
    snapshot = validate_rate(rate)
    listing.exchange_rate_snapshot = snapshot
    listing.normalized_price_kgs = compute_normalized_price_kgs(
        price=listing.price,
        currency=listing.currency,
        snapshot=snapshot,
    )
