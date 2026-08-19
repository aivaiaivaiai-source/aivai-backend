from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SQLEnum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin
from app.models.enums import WalletLedgerKind

if TYPE_CHECKING:
    from app.models.user import User


class WalletLedger(Base, TimestampMixin):
    """Append-only wallet movements. Balance on users is the cached total."""

    __tablename__ = "wallet_ledger"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    delta: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    balance_after: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    kind: Mapped[WalletLedgerKind] = mapped_column(
        SQLEnum(WalletLedgerKind, name="wallet_ledger_kind_enum"),
        nullable=False,
        index=True,
    )
    reference_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    reference_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    user: Mapped[User] = relationship("User")
