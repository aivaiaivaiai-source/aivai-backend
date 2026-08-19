from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException, EntityNotFoundError, RateLimitExceededError
from app.models.ai_message import AiMessage
from app.models.ai_session import AiSession
from app.models.ai_subscription import AiSubscription
from app.models.assistant_enums import AssistantMessageRole
from app.models.enums import AiAgentType, AiMessageType, AiSubscriptionStatus, WalletLedgerKind
from app.models.user import User
from app.services.ai_criteria_parser import parse_search_criteria
from app.services.ai_search_service import AiSearchService
from app.services.wallet_service import WalletService


class AiAgentPolicy:
    PRICE_SOM = 190
    DURATION_DAYS = 7
    MAX_MSG_PER_MIN = 12
    MAX_MSG_PER_DAY = 200
    MAX_CHARS = 1000

    AGENTS: dict[AiAgentType, dict[str, str]] = {
        AiAgentType.ai_realtor: {
            "title": "ИИ Риелтор",
            "subtitle": "Найду недвижимость",
            "icon": "home",
        },
        AiAgentType.ai_auto: {
            "title": "ИИ Автоподбор",
            "subtitle": "Подберу автомобиль",
            "icon": "car",
        },
        AiAgentType.ai_hr: {
            "title": "ИИ HR",
            "subtitle": "Найду работу или сотрудника",
            "icon": "briefcase",
        },
    }


class AiAgentService:
    def __init__(
        self,
        session: AsyncSession,
        wallet: WalletService,
        search: AiSearchService | None = None,
    ) -> None:
        self._session = session
        self._wallet = wallet
        self._search = search

    async def list_agents(self, user_id: int) -> list[dict]:
        subs_result = await self._session.execute(
            select(AiSubscription).where(
                AiSubscription.user_id == user_id,
                AiSubscription.status == AiSubscriptionStatus.active,
            )
        )
        active_subs = {s.agent_type: s for s in subs_result.scalars().all()}

        now = datetime.now(timezone.utc)
        agents: list[dict] = []
        for agent_type, meta in AiAgentPolicy.AGENTS.items():
            sub = active_subs.get(agent_type)
            sub_info = None
            if sub is not None:
                if sub.expires_at <= now:
                    sub.status = AiSubscriptionStatus.expired
                    await self._session.flush()
                else:
                    sub_info = {
                        "id": sub.id,
                        "status": sub.status.value,
                        "starts_at": sub.starts_at,
                        "expires_at": sub.expires_at,
                        "messages_today": sub.messages_today,
                        "max_messages_day": AiAgentPolicy.MAX_MSG_PER_DAY,
                    }
            agents.append({
                "agent_type": agent_type.value,
                "title": meta["title"],
                "subtitle": meta["subtitle"],
                "icon": meta["icon"],
                "price_som": AiAgentPolicy.PRICE_SOM,
                "duration_days": AiAgentPolicy.DURATION_DAYS,
                "subscription": sub_info,
            })
        return agents

    async def subscribe(self, user_id: int, agent_type: AiAgentType) -> AiSubscription:
        existing = await self.check_subscription(user_id, agent_type)
        if existing is not None:
            # Idempotency: already subscribed => return existing subscription.
            # This prevents mobile double-tap / sheet races from breaking the chat flow.
            return existing

        user = await self._session.get(User, user_id)
        if user is None:
            raise EntityNotFoundError("User", entity_id=user_id)

        await self._wallet.debit(
            user,
            Decimal(AiAgentPolicy.PRICE_SOM),
            kind=WalletLedgerKind.ai_subscription_charge,
            reference_type="ai_subscription",
            reference_id="pending",
        )

        now = datetime.now(timezone.utc)
        subscription = AiSubscription(
            user_id=user_id,
            agent_type=agent_type,
            status=AiSubscriptionStatus.active,
            price_som=AiAgentPolicy.PRICE_SOM,
            starts_at=now,
            expires_at=now + timedelta(days=AiAgentPolicy.DURATION_DAYS),
            messages_today=0,
            messages_today_reset=now.date(),
        )
        self._session.add(subscription)
        await self._session.flush()

        session = AiSession(
            user_id=user_id,
            agent_type=agent_type,
            subscription_id=subscription.id,
        )
        self._session.add(session)
        await self._session.flush()

        greeting = self._greeting_for(agent_type)
        self._session.add(
            AiMessage(
                session_id=session.id,
                role=AssistantMessageRole.assistant,
                content=greeting,
                message_type=AiMessageType.text,
                metadata_json={},
            )
        )

        await self._session.commit()
        await self._session.refresh(subscription)
        return subscription

    async def cancel_subscription(
        self, user_id: int, agent_type: AiAgentType,
    ) -> AiSubscription:
        """
        Cancel active subscription without refund.
        This makes the agent unavailable immediately for the user.
        """
        sub = await self.check_subscription(user_id, agent_type)
        if sub is None:
            raise AppException(
                "Нет активной подписки на этого агента.",
                status_code=404,
                code="NO_ACTIVE_SUBSCRIPTION",
            )

        now = datetime.now(timezone.utc)
        sub.status = AiSubscriptionStatus.cancelled
        sub.expires_at = now

        if self._search is not None:
            await self._search.deactivate_tasks_for_subscription(sub.id)

        await self._session.commit()
        await self._session.refresh(sub)
        return sub

    async def get_or_create_session(
        self, user_id: int, agent_type: AiAgentType,
    ) -> AiSession:
        sub = await self.check_subscription(user_id, agent_type)
        if sub is None:
            raise AppException(
                "Нет активной подписки на этого агента.",
                status_code=403,
                code="NO_ACTIVE_SUBSCRIPTION",
            )

        result = await self._session.execute(
            select(AiSession)
            .where(
                AiSession.user_id == user_id,
                AiSession.agent_type == agent_type,
                AiSession.subscription_id == sub.id,
            )
            .order_by(AiSession.created_at.desc())
            .limit(1)
        )
        session = result.scalar_one_or_none()
        if session is not None:
            return session

        session = AiSession(
            user_id=user_id,
            agent_type=agent_type,
            subscription_id=sub.id,
        )
        self._session.add(session)
        await self._session.flush()
        return session

    async def send_message(
        self, user_id: int, agent_type: AiAgentType, text: str,
    ) -> list[AiMessage]:
        sub = await self.check_subscription(user_id, agent_type)
        if sub is None:
            raise AppException(
                "Нет активной подписки на этого агента.",
                status_code=403,
                code="NO_ACTIVE_SUBSCRIPTION",
            )

        if len(text) > AiAgentPolicy.MAX_CHARS:
            raise AppException(
                f"Сообщение слишком длинное (макс. {AiAgentPolicy.MAX_CHARS} символов).",
                status_code=400,
                code="MESSAGE_TOO_LONG",
            )

        today = date.today()
        if sub.messages_today_reset != today:
            sub.messages_today = 0
            sub.messages_today_reset = today

        if sub.messages_today >= AiAgentPolicy.MAX_MSG_PER_DAY:
            raise RateLimitExceededError(
                f"Дневной лимит ({AiAgentPolicy.MAX_MSG_PER_DAY}) сообщений исчерпан.",
            )

        ai_session = await self.get_or_create_session(user_id, agent_type)

        user_msg = AiMessage(
            session_id=ai_session.id,
            role=AssistantMessageRole.user,
            content=text,
            message_type=AiMessageType.text,
            metadata_json={},
        )
        self._session.add(user_msg)

        assistant_messages: list[AiMessage] = []

        if self._search is not None:
            parsed = parse_search_criteria(text, agent_type)
            task = await self._search.upsert_task(
                user_id=user_id,
                agent_type=agent_type,
                subscription_id=sub.id,
                session_id=ai_session.id,
                source_text=text,
                parsed=parsed,
            )
            found = await self._search.search_listings(task)
            reply_text = self._search.build_assistant_reply(agent_type, task, found)
            text_msg = AiMessage(
                session_id=ai_session.id,
                role=AssistantMessageRole.assistant,
                content=reply_text,
                message_type=AiMessageType.text,
                metadata_json={},
            )
            self._session.add(text_msg)
            assistant_messages.append(text_msg)

            for listing in found:
                link_msg = self._search.build_listing_message(listing)
                link_msg.session_id = ai_session.id
                self._session.add(link_msg)
                assistant_messages.append(link_msg)
                await self._search.record_immediate_match(task.id, listing.id)
        else:
            agent_meta = AiAgentPolicy.AGENTS[agent_type]
            stub_text = f"Я {agent_meta['title']}. Функция в разработке."
            assistant_msg = AiMessage(
                session_id=ai_session.id,
                role=AssistantMessageRole.assistant,
                content=stub_text,
                message_type=AiMessageType.text,
                metadata_json={},
            )
            self._session.add(assistant_msg)
            assistant_messages.append(assistant_msg)

        sub.messages_today += 1
        await self._session.commit()
        for msg in assistant_messages:
            await self._session.refresh(msg)
        return assistant_messages

    async def get_history(
        self,
        user_id: int,
        agent_type: AiAgentType,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AiMessage]:
        session_result = await self._session.execute(
            select(AiSession.id).where(
                AiSession.user_id == user_id,
                AiSession.agent_type == agent_type,
            )
        )
        session_ids = [row[0] for row in session_result.all()]
        if not session_ids:
            return []

        result = await self._session.execute(
            select(AiMessage)
            .where(AiMessage.session_id.in_(session_ids))
            .order_by(AiMessage.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def check_subscription(
        self, user_id: int, agent_type: AiAgentType,
    ) -> AiSubscription | None:
        now = datetime.now(timezone.utc)
        result = await self._session.execute(
            select(AiSubscription).where(
                AiSubscription.user_id == user_id,
                AiSubscription.agent_type == agent_type,
                AiSubscription.status == AiSubscriptionStatus.active,
                AiSubscription.expires_at > now,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    def _greeting_for(agent_type: AiAgentType) -> str:
        greetings = {
            AiAgentType.ai_realtor: (
                "Привет! Я ИИ Риелтор. Напишите, какую недвижимость ищете "
                "(район, бюджет, параметры) — и я подберу варианты."
            ),
            AiAgentType.ai_auto: (
                "Привет! Я ИИ Автоподбор. Напишите марку/год/бюджет — "
                "и я подберу подходящие предложения."
            ),
            AiAgentType.ai_hr: (
                "Привет! Я ИИ HR. Расскажите, кого ищете или какую работу "
                "хотите — и я помогу."
            ),
        }
        return greetings.get(
            agent_type,
            "Привет! Я ИИ помощник. Опишите вашу задачу — и я начну подбор.",
        )
