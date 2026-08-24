from __future__ import annotations

import enum


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
