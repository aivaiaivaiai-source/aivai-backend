from __future__ import annotations

import enum


class Currency(str, enum.Enum):
    KGS = "KGS"
    USD = "USD"


class ListingStatus(str, enum.Enum):
    active = "active"
    sold = "sold"
    draft = "draft"


class WalletLedgerKind(str, enum.Enum):
    promotion_charge = "promotion_charge"
    topup = "topup"
    refund = "refund"
    ai_subscription_charge = "ai_subscription_charge"  # legacy ledger entries


class PromotionOrderStatus(str, enum.Enum):
    active = "active"
    stopped = "stopped"
    expired = "expired"
