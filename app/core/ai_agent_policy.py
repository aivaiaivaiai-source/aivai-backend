"""Single source of truth for paid AI search assistants."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.core.exceptions import AppException
from app.models.ai_enums import AiAgentType

SUBSCRIPTION_PRICE_SOM = 190
SUBSCRIPTION_DAYS = 3
MAX_MESSAGES_PER_MINUTE = 8
MAX_MESSAGES_PER_DAY = 100
MAX_MESSAGE_LENGTH = 2000
HISTORY_PAGE_SIZE = 50
HISTORY_MAX_LIMIT = 50
MAX_MATCHES_PER_LISTING = 50

# Root category slugs — descendants are resolved at runtime.
AGENT_CATEGORY_ROOT: dict[AiAgentType, str] = {
    AiAgentType.ai_realtor: "real-estate",
    AiAgentType.ai_auto: "transport",
    AiAgentType.ai_hr: "jobs",
}

AGENT_LABELS: dict[AiAgentType, str] = {
    AiAgentType.ai_realtor: "ИИ Риелтор",
    AiAgentType.ai_auto: "ИИ Автоподбор",
    AiAgentType.ai_hr: "ИИ HR",
}

WELCOME_MESSAGES: dict[AiAgentType, str] = {
    AiAgentType.ai_realtor: (
        "Привет! Я ИИ Риелтор. Напиши, какую недвижимость ищешь: "
        "город, бюджет, комнаты — я сразу поищу и буду следить за новыми объявлениями."
    ),
    AiAgentType.ai_auto: (
        "Привет! Я ИИ Автоподбор. Напиши марку, модель, год, бюджет — "
        "найду подходящие авто и сообщу о новых."
    ),
    AiAgentType.ai_hr: (
        "Привет! Я ИИ HR. Опиши вакансию или работу, которую ищешь: "
        "должность, город, зарплата — буду мониторить новые предложения."
    ),
}


@dataclass(frozen=True)
class SubscriptionWindow:
    starts_at: datetime
    expires_at: datetime
    price_som: int


def subscription_window(*, now: datetime | None = None) -> SubscriptionWindow:
    start = now or datetime.now(UTC)
    return SubscriptionWindow(
        starts_at=start,
        expires_at=start + timedelta(days=SUBSCRIPTION_DAYS),
        price_som=SUBSCRIPTION_PRICE_SOM,
    )


def agent_catalog() -> list[AiAgentType]:
    return list(AiAgentType)


def validate_message_text(text: str) -> str:
    cleaned = text.strip()
    if not cleaned:
        raise AppException("Message cannot be empty.", status_code=400, code="EMPTY_MESSAGE")
    if len(cleaned) > MAX_MESSAGE_LENGTH:
        raise AppException(
            f"Message too long (max {MAX_MESSAGE_LENGTH} chars).",
            status_code=400,
            code="MESSAGE_TOO_LONG",
        )
    return cleaned
