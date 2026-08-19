from decimal import Decimal

from pydantic import BaseModel, Field


class WalletTopup(BaseModel):
    """Placeholder credit until a payment provider is wired."""

    amount: Decimal = Field(..., gt=0, le=Decimal("100000"))
