from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ai_agent_policy import AGENT_CATEGORY_ROOT
from app.core.notifications import NOTIFICATION_TYPE_AI_AGENT_MATCH
from app.models.ai_enums import AiAgentType, AiMessageType
from app.models.assistant_enums import AssistantMessageRole
from app.models.listing import Listing
from app.models.notification import Notification
from app.repositories.ai_agent_repository import AiAgentRepository
from app.repositories.ai_search_task_repository import AiSearchTaskRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.notification_repository import NotificationRepository
from app.schemas.listing import ListingRead
from app.services.ai_realtime_hub import publish_ai_message


class AiSearchService:
    def __init__(
        self,
        session: AsyncSession,
        categories: CategoryRepository,
        tasks: AiSearchTaskRepository,
        agents: AiAgentRepository,
        notifications: NotificationRepository,
    ) -> None:
        self._session = session
        self._categories = categories
        self._tasks = tasks
        self._agents = agents
        self._notifications = notifications
        self._category_cache: dict[str, list[int]] = {}

    async def resolve_category_ids(self, agent_type: AiAgentType) -> list[int]:
        root_slug = AGENT_CATEGORY_ROOT[agent_type]
        cached = self._category_cache.get(root_slug)
        if cached is not None:
            return cached
        root = await self._categories.get_by_slug(root_slug)
        if root is None:
            self._category_cache[root_slug] = []
            return []
        ids = [root.id]
        stack = [root.id]
        while stack:
            parent_id = stack.pop()
            children = await self._categories.get_children_by_parent_id(parent_id)
            for child in children:
                ids.append(child.id)
                stack.append(child.id)
        self._category_cache[root_slug] = ids
        return ids

    async def immediate_search(
        self,
        *,
        agent_type: AiAgentType,
        criteria: dict[str, Any],
        category_ids: list[int],
        limit: int = 5,
    ) -> list[Listing]:
        return await self._tasks.search_listings(criteria, category_ids, limit=limit)

    async def deactivate_tasks_for_subscription(self, subscription_id: int) -> None:
        await self._tasks.deactivate_for_subscription(subscription_id)

    async def upsert_monitoring_task(
        self,
        *,
        user_id: int,
        agent_type: AiAgentType,
        subscription_id: int,
        session_id: int,
        criteria: dict[str, Any],
        category_ids: list[int],
        source_text: str,
    ):
        return await self._tasks.upsert_task(
            user_id=user_id,
            agent_type=agent_type,
            subscription_id=subscription_id,
            session_id=session_id,
            criteria=criteria,
            category_ids=category_ids,
            source_text=source_text,
        )

    async def emit_matches_for_listing(self, listing: Listing) -> None:
        if listing.owner_id is None:
            return
        tasks = await self._tasks.list_active_tasks_for_listing(listing)
        for task in tasks:
            match = await self._tasks.record_match(task.id, listing.id)
            if match is None:
                continue
            listing_read = ListingRead.model_validate(listing)
            content = f"Новое объявление: {listing.title}"
            dedupe_key = f"match:{listing.id}"
            msg = await self._agents.add_message(
                task.session_id,
                role=AssistantMessageRole.assistant,
                content=content,
                message_type=AiMessageType.listing_link,
                metadata={
                    "listing_id": listing.id,
                    "listing": listing_read.model_dump(mode="json"),
                },
                dedupe_key=dedupe_key,
            )
            self._session.add(
                Notification(
                    user_id=task.user_id,
                    title="ИИ-помощник нашёл объявление",
                    body=listing.title,
                    type=NOTIFICATION_TYPE_AI_AGENT_MATCH,
                    payload={
                        "listing_id": str(listing.id),
                        "agent_type": task.agent_type.value,
                        "task_id": str(task.id),
                    },
                    is_read=False,
                )
            )
            await publish_ai_message(
                user_id=task.user_id,
                agent_type=task.agent_type.value,
                payload={
                    "id": msg.id,
                    "role": msg.role.value if hasattr(msg.role, "value") else str(msg.role),
                    "content": msg.content,
                    "message_type": (
                        msg.message_type.value
                        if hasattr(msg.message_type, "value")
                        else str(msg.message_type)
                    ),
                    "metadata": msg.metadata_json or {},
                    "created_at": msg.created_at.isoformat() if msg.created_at else None,
                },
            )
