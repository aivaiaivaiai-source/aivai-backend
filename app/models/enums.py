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
    ai_subscription_charge = "ai_subscription_charge"


class AiAgentType(str, enum.Enum):
    ai_realtor = "ai_realtor"
    ai_auto = "ai_auto"
    ai_hr = "ai_hr"


class AiSubscriptionStatus(str, enum.Enum):
    active = "active"
    expired = "expired"
    cancelled = "cancelled"


class AiMessageType(str, enum.Enum):
    text = "text"
    listing_link = "listing_link"


class PromotionOrderStatus(str, enum.Enum):
    active = "active"
    stopped = "stopped"
    expired = "expired"
