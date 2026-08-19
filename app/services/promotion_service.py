from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException, EntityNotFoundError, OwnershipError, TransactionFailedError
from app.core.promotion_policy import is_active, quote, refund_on_stop
from app.models.enums import ListingStatus, PromotionOrderStatus, WalletLedgerKind
from app.models.promotion_order import PromotionOrder
from app.repositories.listing_repository import ListingRepository
from app.repositories.user_repository import UserRepository
from app.schemas.listing import ListingRead, PromotionStopRead
from app.services.listing_service import ListingService
from app.services.wallet_service import WalletService


class PromotionService:
    def __init__(
        self,
        session: AsyncSession,
        listings: ListingRepository,
        users: UserRepository,
        wallet: WalletService,
        listing_service: ListingService,
    ) -> None:
        self._session = session
        self._listings = listings
        self._users = users
        self._wallet = wallet
        self._listing_service = listing_service

    async def activate(
        self,
        listing_id: int,
        *,
        actor_user_id: int,
        daily_rate: int,
        days: int,
    ) -> ListingRead:
        priced = quote(daily_rate=daily_rate, days=days)
        listing = await self._listings.get_by_id(listing_id, for_update=True)
        if listing is None:
            raise EntityNotFoundError("Listing", entity_id=listing_id)
        if listing.owner_id != actor_user_id:
            raise OwnershipError("You cannot promote another user's listing.")
        if listing.status != ListingStatus.active:
            raise AppException(
                "Only published listings can be promoted",
                status_code=400,
                code="LISTING_NOT_ACTIVE",
            )

        now = datetime.now(UTC)
        await self._close_inactive_window(listing, now=now)
        if is_active(
            is_promoted=listing.is_promoted,
            ends_at=listing.promotion_ends_at,
            now=now,
        ):
            raise AppException(
                "Listing is already promoted. Stop it first to buy a new package.",
                status_code=409,
                code="ALREADY_PROMOTED",
            )

        user = await self._users.get_for_update(actor_user_id)
        if user is None:
            raise EntityNotFoundError("User", entity_id=actor_user_id)

        starts_at, ends_at = priced.window(starts_at=now)
        await self._wallet.debit(
            user,
            Decimal(priced.total),
            kind=WalletLedgerKind.promotion_charge,
            reference_type="listing",
            reference_id=str(listing_id),
        )
        order = PromotionOrder(
            listing_id=listing.id,
            user_id=user.id,
            daily_rate=priced.daily_rate,
            days=priced.days,
            discount_percent=priced.discount_percent,
            total_amount=Decimal(priced.total),
            tier=priced.tier,
            starts_at=starts_at,
            ends_at=ends_at,
            status=PromotionOrderStatus.active,
        )
        self._session.add(order)
        listing.is_promoted = True
        listing.promotion_daily_rate = priced.daily_rate
        listing.promotion_tier = priced.tier
        listing.promotion_starts_at = starts_at
        listing.promotion_ends_at = ends_at
        try:
            await self._session.commit()
        except Exception as exc:
            await self._session.rollback()
            raise TransactionFailedError(
                "Failed to activate promotion; transaction rolled back.",
            ) from exc

        persisted = await self._listings.get_by_id(listing_id)
        if persisted is None:
            raise TransactionFailedError("Listing vanished after promotion.")
        return self._listing_service._to_read(persisted)

    async def stop(self, listing_id: int, *, actor_user_id: int) -> PromotionStopRead:
        listing = await self._listings.get_by_id(listing_id, for_update=True)
        if listing is None:
            raise EntityNotFoundError("Listing", entity_id=listing_id)
        if listing.owner_id != actor_user_id:
            raise OwnershipError("You cannot modify another user's listing.")

        now = datetime.now(UTC)
        if not is_active(
            is_promoted=listing.is_promoted,
            ends_at=listing.promotion_ends_at,
            now=now,
        ):
            raise AppException(
                "Listing is not promoted",
                status_code=400,
                code="NOT_PROMOTED",
            )

        stmt = (
            select(PromotionOrder)
            .where(
                PromotionOrder.listing_id == listing_id,
                PromotionOrder.status == PromotionOrderStatus.active,
            )
            .with_for_update()
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        user = await self._users.get_for_update(actor_user_id)
        if user is None:
            raise EntityNotFoundError("User", entity_id=actor_user_id)

        refund_amount = 0
        charged_days = 0
        refunded_days = 0
        for order in rows:
            paid = int(order.total_amount)
            settled = refund_on_stop(
                paid_total=paid,
                purchased_days=order.days,
                starts_at=order.starts_at,
                now=now,
            )
            order.status = PromotionOrderStatus.stopped
            order.ends_at = now
            order.refunded_amount = Decimal(settled.refund_amount)
            refund_amount += settled.refund_amount
            charged_days += settled.charged_days
            refunded_days += settled.refunded_days
            if settled.refund_amount > 0:
                await self._wallet.credit(
                    user,
                    Decimal(settled.refund_amount),
                    kind=WalletLedgerKind.refund,
                    reference_type="promotion_order",
                    reference_id=str(order.id),
                )

        listing.is_promoted = False
        listing.promotion_tier = 0
        listing.promotion_daily_rate = None
        listing.promotion_ends_at = now
        try:
            await self._session.commit()
        except Exception as exc:
            await self._session.rollback()
            raise TransactionFailedError(
                "Failed to stop promotion; transaction rolled back.",
            ) from exc

        persisted = await self._listings.get_by_id(listing_id)
        if persisted is None:
            raise TransactionFailedError("Listing vanished after stop.")
        return PromotionStopRead(
            listing=self._listing_service._to_read(persisted),
            refund_amount=refund_amount,
            charged_days=charged_days,
            refunded_days=refunded_days,
        )

    async def _close_inactive_window(self, listing, *, now: datetime) -> None:
        """Drop a stale flag / expire leftover orders without charging."""
        if is_active(
            is_promoted=listing.is_promoted,
            ends_at=listing.promotion_ends_at,
            now=now,
        ):
            return
        stmt = (
            select(PromotionOrder)
            .where(
                PromotionOrder.listing_id == listing.id,
                PromotionOrder.status == PromotionOrderStatus.active,
            )
            .with_for_update()
        )
        for order in (await self._session.execute(stmt)).scalars().all():
            order.status = PromotionOrderStatus.expired
        listing.is_promoted = False
        listing.promotion_tier = 0
        listing.promotion_daily_rate = None
