# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class FxRateRead(BaseModel):
    """Current Backend-managed USD→KGS rate (not a listing snapshot)."""

    pair: str = "USD_KGS"
    rate: Decimal
    source: str
    rate_updated_at: datetime


class FxRateUpdate(BaseModel):
    """Admin/internal rate update. Not for marketplace users."""

    rate: Decimal = Field(..., gt=0)
    source: str = Field(default="configured", max_length=64)
