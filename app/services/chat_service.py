from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AppException,
    EntityNotFoundError,
    OwnershipError,
    TransactionFailedError,
)
from app.core.pagination import clamp_limit
from app.models.chat import Chat
from app.models.message import Message
from app.repositories.chat_repository import ChatRepository
from app.repositories.listing_repository import ListingRepository
from app.repositories.media_repository import MediaRepository
from app.repositories.message_repository import MessageRepository
from app.schemas.chat import ChatLastMessageRead, ChatPeerRead, ChatRead
from app.schemas.media import MediaRead
from app.schemas.message import MessageRead
from app.services.storage_service import StorageService

_MAX_CHAT_MEDIA_ATTACHMENTS = 10


class ChatService:
    """All participant checks and messaging business rules live here."""

    def __init__(
        self,
        session: AsyncSession,
        chat_repository: ChatRepository,
        message_repository: MessageRepository,
        listing_repository: ListingRepository,
        media_repository: MediaRepository,
        storage: StorageService,
    ) -> None:
        self._session = session
        self._chats = chat_repository
        self._messages = message_repository
        self._listings = listing_repository
        self._media = media_repository
        self._storage = storage

    @staticmethod
    def _ensure_participant(chat: Chat, user_id: int) -> None:
        if chat.buyer_id != user_id and chat.seller_id != user_id:
            raise OwnershipError("You cannot access another user's conversation.")

    @staticmethod
    def _message_read(model: Message) -> MessageRead:
        ordered = sorted(model.attachments, key=lambda a: a.id)
        return MessageRead(
            id=model.id,
            chat_id=model.chat_id,
            sender_id=model.sender_id,
            text=model.text,
            read_at=model.read_at,
            created_at=model.created_at,
            attachments=[MediaRead.model_validate(a.media) for a in ordered],
        )

    def _chat_read(
        self,
        chat: Chat,
        *,
        unread_count: int,
        current_user_id: int,
        last_message: Message | None = None,
    ) -> ChatRead:
        peer_user = chat.seller if chat.buyer_id == current_user_id else chat.buyer
        peer = (
            ChatPeerRead(id=peer_user.id, full_name=peer_user.full_name)
            if peer_user is not None
            else None
        )
        last = None
        if last_message is not None:
            preview = last_message.text.strip()
            if not preview and last_message.attachments:
                preview = "📷 Фото"
            last = ChatLastMessageRead(
                text=preview,
                created_at=last_message.created_at,
            )
        base = ChatRead.model_validate(chat)
        return base.model_copy(
            update={
                "unread_count": unread_count,
                "peer": peer,
                "last_message": last,
            }
        )

    async def get_or_create_chat_for_listing(
        self,
        listing_id: int,
        *,
        current_user_id: int,
    ) -> ChatRead:
        listing = await self._listings.get_by_id(listing_id)
        if listing is None:
            raise EntityNotFoundError("Listing", entity_id=listing_id)
        seller_id = listing.owner_id
        if seller_id is None:
            raise AppException(
                "This listing has no seller; chat is unavailable.",
                status_code=400,
            )
        if seller_id == current_user_id:
            raise AppException(
                "You cannot start a conversation about your own listing.",
                status_code=400,
            )

        buyer_id = current_user_id
        chat, _created = await self._chats.get_or_create_chat(
            listing_id=listing_id,
            buyer_id=buyer_id,
            seller_id=seller_id,
        )
        try:
            await self._session.commit()
        except Exception as exc:
            await self._session.rollback()
            raise TransactionFailedError(
                "Failed to open chat; transaction rolled back.",
            ) from exc

        loaded = await self._chats.get_by_id_loaded(chat.id)
        if loaded is None:
            raise TransactionFailedError("Chat vanished after creation.")
        unread = await self._messages.count_unread_from_others(loaded.id, current_user_id)
        last = await self._messages.get_last_for_chats([loaded.id])
        return self._chat_read(
            loaded,
            unread_count=unread,
            current_user_id=current_user_id,
            last_message=last.get(loaded.id),
        )

    async def list_chats_for_user(self, *, current_user_id: int) -> list[ChatRead]:
        rows = await self._chats.list_user_chats(current_user_id)
        chat_ids = [chat.id for chat, _ in rows]
        last_by_chat = await self._messages.get_last_for_chats(chat_ids)
        return [
            self._chat_read(
                chat,
                unread_count=unread,
                current_user_id=current_user_id,
                last_message=last_by_chat.get(chat.id),
            )
            for chat, unread in rows
        ]

    async def list_messages(
        self,
        chat_id: int,
        *,
        current_user_id: int,
        limit: int,
        offset: int,
    ) -> list[MessageRead]:
        chat = await self._chats.get_by_id_loaded(chat_id)
        if chat is None:
            raise EntityNotFoundError("Chat", entity_id=chat_id)
        self._ensure_participant(chat, current_user_id)
        limit = clamp_limit(limit)

        await self._messages.mark_as_read_from_others(chat_id, current_user_id)
        msgs = await self._messages.list_by_chat(chat_id, limit=limit, offset=offset)

        try:
            await self._session.commit()
        except Exception as exc:
            await self._session.rollback()
            raise TransactionFailedError(
                "Failed to update read status and fetch messages; transaction rolled back.",
            ) from exc

        return [self._message_read(m) for m in msgs]


    async def send_message(
        self,
        chat_id: int,
        *,
        current_user_id: int,
        text: str,
        media_ids: list[int],
    ) -> MessageRead:
        body = text.strip()
        unique_media_ids = list(dict.fromkeys(media_ids))

        if not body and not unique_media_ids:
            raise AppException(
                "Either non-empty text or at least one media attachment is required.",
                status_code=400,
            )
        if len(unique_media_ids) > _MAX_CHAT_MEDIA_ATTACHMENTS:
            raise AppException(
                f"No more than {_MAX_CHAT_MEDIA_ATTACHMENTS} media attachments per message.",
                status_code=400,
            )

        chat = await self._chats.get_by_id(chat_id)
        if chat is None:
            raise EntityNotFoundError("Chat", entity_id=chat_id)
        self._ensure_participant(chat, current_user_id)

        if unique_media_ids:
            rows = await self._media.get_by_ids(unique_media_ids)
            if len(rows) != len(unique_media_ids):
                raise AppException(
                    "One or more media_ids do not exist.",
                    status_code=400,
                )
            listing_id = chat.listing_id
            for media in rows:
                if media.chat_id is not None and media.chat_id != chat.id:
                    raise AppException(
                        "Attachments must belong to this conversation.",
                        status_code=400,
                    )
                if media.chat_id is None and media.listing_id != listing_id:
                    raise AppException(
                        "Attachments must belong to the listing for this conversation.",
                        status_code=400,
                    )
                if not self._storage.stored_file_exists(media.url):
                    raise AppException(
                        "Attachment file is missing from storage.",
                        status_code=400,
                    )

        message = Message(
            chat_id=chat_id,
            sender_id=current_user_id,
            text=body if body else "",
        )
        chat.last_message_at = datetime.now(UTC)
        await self._messages.create(message)
        if unique_media_ids:
            await self._messages.add_attachments(message_id=message.id, media_ids=unique_media_ids)

        try:
            await self._session.commit()
        except Exception as exc:
            await self._session.rollback()
            raise TransactionFailedError(
                "Failed to send message; transaction rolled back.",
            ) from exc

        hydrated = await self._messages.get_by_id_with_attachments(message.id)
        if hydrated is None:
            raise TransactionFailedError("Message vanished after send.")
        return self._message_read(hydrated)

    async def upload_attachments(
        self,
        chat_id: int,
        *,
        current_user_id: int,
        payloads: list[tuple[bytes, str, str | None]],
    ) -> list[MediaRead]:
        if not payloads:
            raise AppException("At least one file is required.", status_code=400)

        chat = await self._chats.get_by_id(chat_id)
        if chat is None:
            raise EntityNotFoundError("Chat", entity_id=chat_id)
        self._ensure_participant(chat, current_user_id)

        existing = await self._media.list_by_chat(chat_id)
        next_order_base = max((m.order for m in existing), default=-1) + 1

        saved_urls: list[str] = []
        try:
            created_rows = []
            for idx, (content, content_type, source_name) in enumerate(payloads):
                url = self._storage.save_image(content, content_type)
                saved_urls.append(url)
                row = Media(
                    url=url,
                    listing_id=chat.listing_id,
                    chat_id=chat.id,
                    order=next_order_base + idx,
                )
                created = await self._media.create(row)
                refreshed = await self._media.get_by_id(created.id)
                if refreshed is not None:
                    created_rows.append(refreshed)

            await self._session.commit()
            return [MediaRead.model_validate(m) for m in created_rows]
        except AppException:
            await self._session.rollback()
            for url in saved_urls:
                self._storage.delete_file(url)
            raise
        except Exception as exc:
            await self._session.rollback()
            for url in saved_urls:
                self._storage.delete_file(url)
            raise TransactionFailedError(
                "Failed to upload chat attachments; transaction rolled back.",
            ) from exc

