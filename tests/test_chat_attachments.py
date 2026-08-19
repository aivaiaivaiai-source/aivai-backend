from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from httpx import AsyncClient

from app.api.deps import get_chat_service, get_current_user
from app.main import app as fastapi_app
from app.models.image_moderation_enums import MediaModerationStatus
from app.schemas.media import MediaRead
from app.schemas.user import UserRead


async def _user() -> UserRead:
    now = datetime.now(UTC)
    return UserRead(
        id=1,
        phone="+79001234567",
        full_name="Dev",
        is_active=True,
        balance=Decimal("0"),
        last_login=None,
        created_at=now,
        updated_at=now,
    )


class _ChatSvc:
    def __init__(self) -> None:
        self.chat_id: int | None = None
        self.user_id: int | None = None
        self.payloads: list[tuple[bytes, str, str | None]] = []

    async def upload_attachments(
        self,
        chat_id: int,
        *,
        current_user_id: int,
        payloads: list[tuple[bytes, str, str | None]],
    ) -> list[MediaRead]:
        self.chat_id = chat_id
        self.user_id = current_user_id
        self.payloads = payloads
        now = datetime.now(UTC)
        return [
            MediaRead(
                id=17,
                listing_id=16,
                url="/media/chat-photo.jpg",
                order=0,
                is_placeholder=False,
                moderation_status=MediaModerationStatus.approved,
                moderation_reason=None,
                moderated_at=now,
            )
        ]


@pytest.mark.asyncio
async def test_chat_attachment_upload_requires_auth(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/chats/16/attachments",
        files={"files": ("chat.jpg", b"\xff\xd8\xff\xdb", "image/jpeg")},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_chat_attachment_upload_forwards_payloads(client: AsyncClient) -> None:
    svc = _ChatSvc()
    fastapi_app.dependency_overrides[get_current_user] = _user
    fastapi_app.dependency_overrides[get_chat_service] = lambda: svc
    resp = await client.post(
        "/api/v1/chats/16/attachments",
        files={"files": ("chat.jpg", b"\xff\xd8\xff\xdb", "image/jpeg")},
    )
    assert resp.status_code == 201
    assert resp.json()[0]["id"] == 17
    assert svc.chat_id == 16
    assert svc.user_id == 1
    assert len(svc.payloads) == 1
    assert svc.payloads[0][1] == "image/jpeg"
    assert svc.payloads[0][2] == "chat.jpg"
