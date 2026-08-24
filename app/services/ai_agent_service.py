from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ai_agent_policy import (
    AGENT_LABELS,
    MAX_MESSAGES_PER_DAY,
    MAX_MESSAGES_PER_MINUTE,
    SUBSCRIPTION_DAYS,
    SUBSCRIPTION_PRICE_SOM,
    WELCOME_MESSAGES,
    agent_catalog,
    subscription_window,
    validate_message_text,
)
from app.core.exceptions import (
    AppException,
    InsufficientBalanceError,
    RateLimitExceededError,
    TransactionFailedError,
)
from app.models.ai_enums import AiAgentType, AiMessageType, AiSubscriptionStatus
from app.models.assistant_enums import AssistantMessageRole
from app.models.enums import WalletLedgerKind
from app.repositories.ai_agent_repository import AiAgentRepository
from app.repositories.user_repository import UserRepository
from app.schemas.ai_agent import (
    AiAgentInfo,
    AiMessageRead,
    AiSendMessageResponse,
    AiSubscriptionRead,
)
from app.schemas.listing import ListingRead
from app.services.ai_criteria_parser import parse_criteria
from app.services.ai_search_service import AiSearchService
from app.services.wallet_service import WalletService


class AiAgentService:
    def __init__(
        self,
        session: AsyncSession,
        agents: AiAgentRepository,
        users: UserRepository,
        wallet: WalletService,
        search: AiSearchService,
    ) -> None:
        self._session = session
        self._agents = agents
        self._users = users
        self._wallet = wallet
        self._search = search

    async def list_agents(self, user_id: int) -> list[AiAgentInfo]:
        await self._agents.expire_stale_subscriptions(user_id)
        items: list[AiAgentInfo] = []
        for agent_type in agent_catalog():
            sub = await self._agents.get_active_subscription(user_id, agent_type)
            unread = 0
            if sub is not None:
                session = await self._agents.get_or_create_session(
                    user_id,
                    agent_type,
                    subscription_id=sub.id,
                )
                unread = await self._agents.count_unread_assistant_messages(
                    session.id,
                    after_message_id=session.last_read_message_id,
                )
            items.append(
                AiAgentInfo(
                    agent_type=agent_type,
                    title=AGENT_LABELS[agent_type],
                    price_som=SUBSCRIPTION_PRICE_SOM,
                    duration_days=SUBSCRIPTION_DAYS,
                    subscribed=sub is not None,
                    subscription=AiSubscriptionRead.model_validate(sub) if sub else None,
                    unread_count=unread,
                )
            )
        return items

    async def get_subscription(self, user_id: int, agent_type: AiAgentType) -> AiSubscriptionRead | None:
        await self._agents.expire_stale_subscriptions(user_id)
        sub = await self._agents.get_active_subscription(user_id, agent_type)
        return AiSubscriptionRead.model_validate(sub) if sub else None

    async def subscribe(self, user_id: int, agent_type: AiAgentType) -> AiSubscriptionRead:
        await self._agents.expire_stale_subscriptions(user_id)
        existing = await self._agents.get_active_subscription(user_id, agent_type, for_update=True)
        if existing is not None:
            raise AppException(
                "Subscription already active.",
                status_code=409,
                code="ALREADY_SUBSCRIBED",
            )

        user = await self._users.get_for_update(user_id)
        if user is None:
            raise AppException("User not found.", status_code=404)

        window = subscription_window()
        try:
            await self._wallet.debit(
                user,
                Decimal(window.price_som),
                kind=WalletLedgerKind.ai_subscription_charge,
                reference_type="ai_agent",
                reference_id=agent_type.value,
            )
            from app.models.ai_subscription import AiSubscription

            sub = AiSubscription(
                user_id=user_id,
                agent_type=agent_type,
                status=AiSubscriptionStatus.active,
                price_som=window.price_som,
                starts_at=window.starts_at,
                expires_at=window.expires_at,
            )
            self._session.add(sub)
            await self._session.flush()

            session = await self._agents.get_or_create_session(
                user_id,
                agent_type,
                subscription_id=sub.id,
            )
            await self._agents.add_message(
                session.id,
                role=AssistantMessageRole.assistant,
                content=WELCOME_MESSAGES[agent_type],
                message_type=AiMessageType.text,
            )
            await self._agents.mark_session_read(session)
            await self._session.commit()
        except InsufficientBalanceError:
            await self._session.rollback()
            raise
        except Exception as exc:
            await self._session.rollback()
            raise TransactionFailedError(
                "Failed to subscribe; transaction rolled back.",
            ) from exc

        refreshed = await self._agents.get_active_subscription(user_id, agent_type)
        if refreshed is None:
            raise TransactionFailedError("Subscription missing after commit.")
        return AiSubscriptionRead.model_validate(refreshed)

    async def cancel(self, user_id: int, agent_type: AiAgentType) -> AiSubscriptionRead:
        sub = await self._agents.get_active_subscription(user_id, agent_type, for_update=True)
        if sub is None:
            raise AppException("No active subscription.", status_code=404, code="NO_SUBSCRIPTION")
        sub.status = AiSubscriptionStatus.cancelled
        await self._search.deactivate_tasks_for_subscription(sub.id)
        try:
            await self._session.commit()
        except Exception as exc:
            await self._session.rollback()
            raise TransactionFailedError("Failed to cancel subscription.") from exc
        return AiSubscriptionRead.model_validate(sub)

    async def history(
        self,
        user_id: int,
        agent_type: AiAgentType,
        *,
        before_id: int | None = None,
        after_id: int | None = None,
        limit: int = 50,
    ) -> list[AiMessageRead]:
        session = await self._agents.get_or_create_session(user_id, agent_type)
        rows = await self._agents.list_messages(
            session.id,
            before_id=before_id,
            after_id=after_id,
            limit=limit,
        )
        # Opening the latest page marks the thread as read (like buyer/seller chat).
        if before_id is None and after_id is None:
            await self._agents.mark_session_read(session)
            try:
                await self._session.commit()
            except Exception as exc:
                await self._session.rollback()
                raise TransactionFailedError(
                    "Failed to update AI read cursor.",
                ) from exc
        return [self._to_message_read(m) for m in rows]

    async def delete_message(
        self,
        user_id: int,
        agent_type: AiAgentType,
        message_id: int,
    ) -> None:
        session = await self._agents.get_or_create_session(user_id, agent_type)
        message = await self._agents.get_message(session.id, message_id)
        if message is None:
            raise AppException("Message not found.", status_code=404, code="MESSAGE_NOT_FOUND")
        if message.role != AssistantMessageRole.user:
            raise AppException(
                "Only your own messages can be deleted.",
                status_code=403,
                code="DELETE_OWN_ONLY",
            )
        await self._agents.delete_message(message)
        try:
            await self._session.commit()
        except Exception as exc:
            await self._session.rollback()
            raise TransactionFailedError("Failed to delete message.") from exc

    async def send_message(
        self,
        user_id: int,
        agent_type: AiAgentType,
        text: str,
    ) -> AiSendMessageResponse:
        cleaned = validate_message_text(text)
        await self._agents.expire_stale_subscriptions(user_id)
        sub = await self._agents.get_active_subscription(user_id, agent_type, for_update=True)
        if sub is None:
            raise AppException(
                "Active subscription required.",
                status_code=402,
                code="SUBSCRIPTION_REQUIRED",
            )

        session = await self._agents.get_or_create_session(user_id, agent_type, subscription_id=sub.id)
        await self._enforce_rate_limits(session.id, sub)

        user_msg = await self._agents.add_message(
            session.id,
            role=AssistantMessageRole.user,
            content=cleaned,
            message_type=AiMessageType.text,
        )
        await self._agents.bump_daily_counter(sub)

        criteria = parse_criteria(cleaned, agent_type=agent_type.value)
        category_ids = await self._search.resolve_category_ids(agent_type)
        listings = await self._search.immediate_search(
            agent_type=agent_type,
            criteria=criteria,
            category_ids=category_ids,
        )
        await self._search.upsert_monitoring_task(
            user_id=user_id,
            agent_type=agent_type,
            subscription_id=sub.id,
            session_id=session.id,
            criteria=criteria,
            category_ids=category_ids,
            source_text=cleaned,
        )

        assistant_messages: list[AiMessageRead] = []
        if listings:
            summary = await self._agents.add_message(
                session.id,
                role=AssistantMessageRole.assistant,
                content=f"Нашёл {len(listings)} подходящих объявлений:",
                message_type=AiMessageType.text,
            )
            assistant_messages.append(self._to_message_read(summary))
            for listing in listings:
                listing_read = ListingRead.model_validate(listing)
                msg = await self._agents.add_message(
                    session.id,
                    role=AssistantMessageRole.assistant,
                    content=listing.title,
                    message_type=AiMessageType.listing_link,
                    metadata={"listing_id": listing.id, "listing": listing_read.model_dump(mode="json")},
                )
                assistant_messages.append(self._to_message_read(msg))
        else:
            reply = await self._agents.add_message(
                session.id,
                role=AssistantMessageRole.assistant,
                content=(
                    "Понял запрос. Пока точных совпадений нет — продолжаю мониторить "
                    "и сообщу, когда появится подходящее объявление."
                ),
                message_type=AiMessageType.text,
            )
            assistant_messages.append(self._to_message_read(reply))

        try:
            await self._session.commit()
        except Exception as exc:
            await self._session.rollback()
            raise TransactionFailedError("Failed to send message.") from exc

        return AiSendMessageResponse(
            user_message=self._to_message_read(user_msg),
            assistant_messages=assistant_messages,
        )

    async def _enforce_rate_limits(self, session_id: int, sub) -> None:
        if sub.messages_today >= MAX_MESSAGES_PER_DAY:
            raise RateLimitExceededError("Daily message limit reached.")
        since = datetime.now(UTC) - timedelta(minutes=1)
        recent = await self._agents.count_recent_user_messages(session_id, since=since)
        if recent >= MAX_MESSAGES_PER_MINUTE:
            raise RateLimitExceededError("Too many messages. Please wait a minute.")

    @staticmethod
    def _to_message_read(message) -> AiMessageRead:
        return AiMessageRead(
            id=message.id,
            role=message.role.value,
            content=message.content,
            message_type=message.message_type.value,
            metadata=message.metadata_json or {},
            created_at=message.created_at,
        )
