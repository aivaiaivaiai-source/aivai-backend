from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import WalletLedgerKind


class WalletTopup(BaseModel):
    """Placeholder credit until a payment provider is wired."""

    amount: Decimal = Field(..., gt=0, le=Decimal("100000"))


class WalletLedgerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    delta: Decimal
    balance_after: Decimal
    kind: WalletLedgerKind
    reference_type: str | None = None
    reference_id: str | None = None
    created_at: datetime
