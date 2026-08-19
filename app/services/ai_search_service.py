from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.notifications import NOTIFICATION_TYPE_AI_AGENT_MATCH
from app.models.ai_message import AiMessage
from app.models.ai_search_task import AiSearchTask
from app.models.assistant_enums import AssistantMessageRole
from app.models.enums import AiAgentType, AiMessageType, Currency, ListingStatus
from app.models.listing import Listing
from app.models.notification import Notification
from app.repositories.ai_search_task_repository import AiSearchTaskRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.listing_repository import ListingRepository
from app.repositories.notification_repository import NotificationRepository
from app.services.ai_criteria_parser import (
    agent_domain_slugs,
    criteria_summary,
    merge_criteria,
    parse_search_criteria,
)


class AiSearchService:
    IMMEDIATE_RESULTS_LIMIT = 5

    def __init__(
        self,
        session: AsyncSession,
        tasks: AiSearchTaskRepository,
        listings: ListingRepository,
        categories: CategoryRepository,
        notifications: NotificationRepository,
    ) -> None:
        self._session = session
        self._tasks = tasks
        self._listings = listings
        self._categories = categories
        self._notifications = notifications

    async def resolve_category_ids(self, agent_type: AiAgentType) -> list[int]:
        ids: list[int] = []
        for slug in agent_domain_slugs(agent_type):
            cat = await self._categories.get_by_slug(slug)
            if cat is not None:
                ids.append(cat.id)
        return ids

    async def upsert_task(
        self,
        *,
        user_id: int,
        agent_type: AiAgentType,
        subscription_id: int,
        session_id: int,
        source_text: str,
        parsed: dict[str, Any],
    ) -> AiSearchTask:
        category_ids = await self.resolve_category_ids(agent_type)
        existing = await self._tasks.get_active_for_session(session_id)
        if existing is not None:
            existing.criteria_json = merge_criteria(existing.criteria_json, parsed)
            existing.source_text = source_text
            existing.category_ids = category_ids
            existing.is_active = True
            await self._session.flush()
            return existing

        task = AiSearchTask(
            user_id=user_id,
            agent_type=agent_type,
            subscription_id=subscription_id,
            session_id=session_id,
            criteria_json=parsed,
            category_ids=category_ids,
            is_active=True,
            source_text=source_text,
        )
        self._session.add(task)
        await self._session.flush()
        return task

    async def search_listings(
        self,
        task: AiSearchTask,
        *,
        limit: int | None = None,
    ) -> list[Listing]:
        criteria = task.criteria_json if isinstance(task.criteria_json, dict) else {}
        limit = limit or self.IMMEDIATE_RESULTS_LIMIT

        currency_raw = criteria.get("currency")
        currency = None
        if currency_raw:
            try:
                currency = Currency(str(currency_raw))
            except ValueError:
                currency = None

        min_price = _to_decimal(criteria.get("min_price"))
        max_price = _to_decimal(criteria.get("max_price"))

        q = criteria.get("q")
        if isinstance(q, str):
            q = q.strip() or None

        return await self._listings.search_listings(
            category_ids=task.category_ids or None,
            min_price=min_price,
            max_price=max_price,
            currency=currency,
            status=ListingStatus.active,
            q=q if isinstance(q, str) else None,
            brand=criteria.get("brand"),
            model=criteria.get("model"),
            year_min=criteria.get("year_min"),
            year_max=criteria.get("year_max"),
            steering=criteria.get("steering"),
            limit=limit,
            offset=0,
        )

    def build_assistant_reply(
        self,
        agent_type: AiAgentType,
        task: AiSearchTask,
        found: list[Listing],
    ) -> str:
        summary = criteria_summary(task.criteria_json, agent_type)
        if found:
            return (
                f"Понял запрос: {summary}.\n"
                f"Нашёл {len(found)} подходящих объявлений прямо сейчас. "
                f"Буду следить за новыми вариантами в течение вашей подписки."
            )
        return (
            f"Понял запрос: {summary}.\n"
            f"Пока точных совпадений нет, но я сохранил критерии и буду "
            f"присылать новые объявления, как только они появятся."
        )

    def build_listing_message(
        self,
        listing: Listing,
        *,
        is_new: bool = False,
    ) -> AiMessage:
        prefix = "Новое объявление" if is_new else "Подходящее объявление"
        return AiMessage(
            session_id=0,  # caller must set
            role=AssistantMessageRole.assistant,
            content=f"{prefix}: {listing.title}",
            message_type=AiMessageType.listing_link,
            metadata_json={
                "listing_id": listing.id,
                "title": listing.title,
                "price": str(listing.price),
                "currency": listing.currency.value,
            },
        )

    async def emit_matches_for_listing(self, listing: Listing) -> int:
        """Background monitor hook: match new listing against active AI tasks."""
        if listing.status != ListingStatus.active or listing.owner_id is None:
            return 0

        matches = await self._tasks.find_matching_for_listing(listing)
        emitted = 0
        for task in matches:
            if await self._tasks.match_exists(task.id, listing.id):
                continue

            msg = self.build_listing_message(listing, is_new=True)
            msg.session_id = task.session_id
            self._session.add(msg)

            notification = Notification(
                user_id=task.user_id,
                title=self._notification_title(task.agent_type),
                body=listing.title,
                type=NOTIFICATION_TYPE_AI_AGENT_MATCH,
                payload={
                    "listing_id": str(listing.id),
                    "agent_type": task.agent_type.value,
                    "task_id": str(task.id),
                },
                is_read=False,
            )
            self._session.add(notification)
            await self._tasks.record_match(task.id, listing.id)
            emitted += 1
        return emitted

    async def deactivate_tasks_for_subscription(self, subscription_id: int) -> None:
        await self._tasks.deactivate_for_subscription(subscription_id)

    async def record_immediate_match(self, task_id: int, listing_id: int) -> None:
        if not await self._tasks.match_exists(task_id, listing_id):
            await self._tasks.record_match(task_id, listing_id)

    @staticmethod
    def _notification_title(agent_type: AiAgentType) -> str:
        return {
            AiAgentType.ai_realtor: "ИИ Риелтор нашёл объявление",
            AiAgentType.ai_auto: "ИИ Автоподбор нашёл объявление",
            AiAgentType.ai_hr: "ИИ HR нашёл объявление",
        }.get(agent_type, "ИИ помощник нашёл объявление")


def _to_decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except Exception:
        return None
