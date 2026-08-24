from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from sqlalchemy import and_, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_enums import AiAgentType, AiSubscriptionStatus
from app.models.ai_message import AiMessage
from app.models.ai_session import AiSession
from app.models.ai_subscription import AiSubscription
from app.models.assistant_enums import AssistantMessageRole
from app.repositories.base import BaseRepository


class AiAgentRepository(BaseRepository[AiSubscription]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, AiSubscription)

    async def get_active_subscription(
        self,
        user_id: int,
        agent_type: AiAgentType,
        *,
        for_update: bool = False,
    ) -> AiSubscription | None:
        now = datetime.now(UTC)
        stmt = (
            select(AiSubscription)
            .where(
                AiSubscription.user_id == user_id,
                AiSubscription.agent_type == agent_type,
                AiSubscription.status == AiSubscriptionStatus.active,
                AiSubscription.expires_at > now,
            )
            .order_by(AiSubscription.id.desc())
            .limit(1)
        )
        if for_update:
            stmt = stmt.with_for_update()
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def expire_stale_subscriptions(self, user_id: int) -> None:
        now = datetime.now(UTC)
        stmt = select(AiSubscription).where(
            AiSubscription.user_id == user_id,
            AiSubscription.status == AiSubscriptionStatus.active,
            AiSubscription.expires_at <= now,
        )
        result = await self._session.execute(stmt)
        for row in result.scalars():
            row.status = AiSubscriptionStatus.expired

    async def get_or_create_session(
        self,
        user_id: int,
        agent_type: AiAgentType,
        *,
        subscription_id: int | None = None,
    ) -> AiSession:
        stmt = select(AiSession).where(
            AiSession.user_id == user_id,
            AiSession.agent_type == agent_type,
        )
        result = await self._session.execute(stmt)
        session = result.scalar_one_or_none()
        if session is not None:
            if subscription_id is not None:
                session.subscription_id = subscription_id
            return session
        session = AiSession(
            user_id=user_id,
            agent_type=agent_type,
            subscription_id=subscription_id,
        )
        self._session.add(session)
        await self._session.flush()
        return session

    async def add_message(
        self,
        session_id: int,
        *,
        role: AssistantMessageRole,
        content: str,
        message_type,
        metadata: dict | None = None,
        dedupe_key: str | None = None,
    ) -> AiMessage:
        if dedupe_key:
            existing_stmt = (
                select(AiMessage)
                .where(
                    AiMessage.session_id == session_id,
                    AiMessage.dedupe_key == dedupe_key,
                )
                .limit(1)
            )
            existing = (await self._session.execute(existing_stmt)).scalar_one_or_none()
            if existing is not None:
                return existing

        msg = AiMessage(
            session_id=session_id,
            role=role,
            content=content,
            message_type=message_type,
            metadata_json=metadata or {},
            dedupe_key=dedupe_key,
        )
        try:
            async with self._session.begin_nested():
                self._session.add(msg)
                await self._session.flush()
        except IntegrityError:
            if dedupe_key:
                existing_stmt = (
                    select(AiMessage)
                    .where(
                        AiMessage.session_id == session_id,
                        AiMessage.dedupe_key == dedupe_key,
                    )
                    .limit(1)
                )
                existing = (await self._session.execute(existing_stmt)).scalar_one_or_none()
                if existing is not None:
                    return existing
            raise
        return msg

    async def list_messages(
        self,
        session_id: int,
        *,
        before_id: int | None = None,
        after_id: int | None = None,
        limit: int = 50,
    ) -> list[AiMessage]:
        stmt = select(AiMessage).where(AiMessage.session_id == session_id)
        if after_id is not None:
            stmt = stmt.where(AiMessage.id > after_id).order_by(AiMessage.id.asc()).limit(limit)
            result = await self._session.execute(stmt)
            return list(result.scalars())
        if before_id is not None:
            stmt = stmt.where(AiMessage.id < before_id)
        stmt = stmt.order_by(AiMessage.id.desc()).limit(limit)
        result = await self._session.execute(stmt)
        rows = list(result.scalars())
        rows.reverse()
        return rows

    async def count_recent_user_messages(
        self,
        session_id: int,
        *,
        since: datetime,
    ) -> int:
        stmt = (
            select(func.count())
            .select_from(AiMessage)
            .where(
                AiMessage.session_id == session_id,
                AiMessage.role == AssistantMessageRole.user,
                AiMessage.created_at >= since,
            )
        )
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    async def bump_daily_counter(self, subscription: AiSubscription) -> None:
        today = date.today()
        if subscription.messages_today_reset != today:
            subscription.messages_today = 0
            subscription.messages_today_reset = today
        subscription.messages_today += 1

    async def count_unread_assistant_messages(
        self,
        session_id: int,
        *,
        after_message_id: int | None,
    ) -> int:
        stmt = (
            select(func.count())
            .select_from(AiMessage)
            .where(
                AiMessage.session_id == session_id,
                AiMessage.role == AssistantMessageRole.assistant,
            )
        )
        if after_message_id is not None:
            stmt = stmt.where(AiMessage.id > after_message_id)
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    async def latest_message_id(self, session_id: int) -> int | None:
        stmt = (
            select(func.max(AiMessage.id))
            .where(AiMessage.session_id == session_id)
        )
        result = await self._session.execute(stmt)
        value = result.scalar_one_or_none()
        return int(value) if value is not None else None

    async def mark_session_read(
        self,
        session: AiSession,
        *,
        up_to_message_id: int | None = None,
    ) -> None:
        if up_to_message_id is None:
            up_to_message_id = await self.latest_message_id(session.id)
        if up_to_message_id is None:
            return
        current = session.last_read_message_id or 0
        if up_to_message_id > current:
            session.last_read_message_id = up_to_message_id

    async def get_message(
        self,
        session_id: int,
        message_id: int,
    ) -> AiMessage | None:
        stmt = (
            select(AiMessage)
            .where(
                AiMessage.session_id == session_id,
                AiMessage.id == message_id,
            )
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_message(self, message: AiMessage) -> None:
        await self._session.delete(message)
        await self._session.flush()
