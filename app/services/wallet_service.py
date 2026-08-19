from __future__ import annotations

from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InsufficientBalanceError, TransactionFailedError
from app.models.enums import WalletLedgerKind
from app.models.user import User
from app.models.wallet_ledger import WalletLedger


class WalletService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def credit(
        self,
        user: User,
        amount: Decimal,
        *,
        kind: WalletLedgerKind,
        reference_type: str | None = None,
        reference_id: str | None = None,
    ) -> User:
        if amount <= 0:
            return user
        user.balance = (user.balance or Decimal("0")) + amount
        self._session.add(
            WalletLedger(
                user_id=user.id,
                delta=amount,
                balance_after=user.balance,
                kind=kind,
                reference_type=reference_type,
                reference_id=reference_id,
            )
        )
        await self._session.flush()
        return user

    async def debit(
        self,
        user: User,
        amount: Decimal,
        *,
        kind: WalletLedgerKind,
        reference_type: str | None = None,
        reference_id: str | None = None,
    ) -> User:
        if amount <= 0:
            return user
        balance = user.balance or Decimal("0")
        if balance < amount:
            raise InsufficientBalanceError(
                balance=balance,
                required_amount=amount,
                shortfall=amount - balance,
            )
        user.balance = balance - amount
        self._session.add(
            WalletLedger(
                user_id=user.id,
                delta=-amount,
                balance_after=user.balance,
                kind=kind,
                reference_type=reference_type,
                reference_id=reference_id,
            )
        )
        await self._session.flush()
        return user

    async def topup(self, user: User, amount: Decimal) -> User:
        try:
            await self.credit(user, amount, kind=WalletLedgerKind.topup)
            await self._session.commit()
        except Exception as exc:
            await self._session.rollback()
            raise TransactionFailedError(
                "Failed to top up wallet; transaction rolled back.",
            ) from exc
        await self._session.refresh(user)
        return user
