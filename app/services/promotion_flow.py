from __future__ import annotations

import re
from decimal import Decimal

from app.core.listing_assistant_rules import PROMOTION_CURRENCY, PROMOTION_PRICE_KGS
from app.schemas.listing_assistant import PromotionOffer, PromotionResult
from app.schemas.user import UserRead
from app.schemas.voice import VoiceCommandResponse, VoiceIntent
from app.services.voice_response_builder import VoiceResponseBuilder

_PROMOTION_YES = re.compile(
    r"(?:да,? продвин|хочу продвин|продвинуть|включи продвижение|давай продвин)",
    re.IGNORECASE,
)
_PROMOTION_NO = re.compile(
    r"(?:нет|не надо|пока нет|не хочу|не нужно|пропустить|skip)",
    re.IGNORECASE,
)


class PromotionFlow:
    """Architecture-only promotion / balance flow (no real payments)."""

    @staticmethod
    def build_offer(listing_id: int) -> PromotionOffer:
        return PromotionOffer(
            enabled=True,
            price_kgs=PROMOTION_PRICE_KGS,
            listing_id=listing_id,
            message=(
                "Хотите продвинуть объявление, чтобы его увидело больше людей? "
                f"Стоимость — {PROMOTION_PRICE_KGS} сом."
            ),
        )

    @classmethod
    def evaluate_acceptance(cls, text: str) -> str | None:
        """Return 'yes', 'no', or None if unclear."""
        raw = text.strip()
        if not raw:
            return None
        if _PROMOTION_YES.search(raw):
            return "yes"
        if _PROMOTION_NO.search(raw):
            return "no"
        return None

    @classmethod
    def handle_response(
        cls,
        intent: VoiceIntent,
        *,
        user: UserRead,
        listing_id: int,
        text: str,
    ) -> VoiceCommandResponse:
        decision = cls.evaluate_acceptance(text)
        if decision is None:
            offer = cls.build_offer(listing_id)
            return VoiceResponseBuilder.promotion_pending(
                intent,
                offer=offer,
                message="Ответьте «да» для продвижения или «нет», чтобы пропустить.",
            )

        if decision == "no":
            return VoiceResponseBuilder.promotion_declined(intent)

        balance = user.balance
        price = PROMOTION_PRICE_KGS
        if balance >= price:
            result = PromotionResult(
                activated=True,
                balance=str(balance),
                required_amount=str(price),
                message="Продвижение подключено. Объявление будет показываться чаще в ленте.",
            )
            return VoiceResponseBuilder.promotion_activated(intent, result, listing_id=listing_id)

        shortfall = price - balance
        result = PromotionResult(
            activated=False,
            topup_required=True,
            balance=str(balance),
            required_amount=str(price),
            message=(
                f"На балансе {balance} {PROMOTION_CURRENCY}, нужно {price} {PROMOTION_CURRENCY}. "
                f"Пополните баланс на {shortfall} {PROMOTION_CURRENCY}, чтобы включить продвижение."
            ),
        )
        return VoiceResponseBuilder.topup_required(intent, result, listing_id=listing_id)
