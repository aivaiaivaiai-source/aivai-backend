from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import clamp_limit
from app.core.exceptions import TransactionFailedError
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserRead


class UserService:
    def __init__(self, session: AsyncSession, user_repository: UserRepository) -> None:
        self._session = session
        self._users = user_repository

    async def list_users(self, limit: int = 100, offset: int = 0) -> list[UserRead]:
        limit = clamp_limit(limit)
        rows = await self._users.get_all(limit=limit, offset=offset)
        return [UserRead.model_validate(u) for u in rows]

    async def get_user_by_id(self, user_id: int) -> UserRead | None:
        row = await self._users.get_by_id(user_id)
        if row is None:
            return None
        return UserRead.model_validate(row)

    async def get_or_create_user_by_phone(self, phone: str, full_name: str) -> UserRead:
        normalized_phone = phone.strip()
        user = await self._users.get_by_phone(normalized_phone)
        if user is not None:
            return UserRead.model_validate(user)

        created = await self._users.create(
            User(phone=normalized_phone, full_name=full_name.strip() or "User")
        )
        try:
            await self._session.commit()
        except Exception as exc:
            await self._session.rollback()
            raise TransactionFailedError(
                "Failed to create user; transaction rolled back.",
            ) from exc
        await self._session.refresh(created)
        return UserRead.model_validate(created)
