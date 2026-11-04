# -*- coding: utf-8 -*-
"""Backend-managed current FX rate (USD→KGS). Listing snapshots are separate."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base, TimestampMixin

# Singleton row key for the marketplace USD→KGS rate.
FX_PAIR_USD_KGS = "USD_KGS"


class FxRate(Base, TimestampMixin):
    __tablename__ = "fx_rates"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    pair: Mapped[str] = mapped_column(String(16), unique=True, nullable=False, index=True)
    rate: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False, default="configured")
    rate_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
