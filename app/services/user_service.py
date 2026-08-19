from __future__ import annotations

from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AppException,
    EntityNotFoundError,
    OwnershipError,
    TransactionFailedError,
)
from app.core.pagination import clamp_limit
from app.models.review import Review
from app.models.user import User
from app.repositories.listing_repository import ListingRepository
from app.repositories.review_repository import ReviewRepository
from app.repositories.user_repository import UserRepository
from app.schemas.review import ReviewRead
from app.schemas.user import UserRead, UserUpdate
from app.services.storage_service import StorageService
from app.services.wallet_service import WalletService


class UserService:
    def __init__(
        self,
        session: AsyncSession,
        user_repository: UserRepository,
        listing_repository: ListingRepository | None = None,
        review_repository: ReviewRepository | None = None,
        storage: StorageService | None = None,
    ) -> None:
        self._session = session
        self._users = user_repository
        self._listings = listing_repository
        self._reviews = review_repository
        self._storage = storage

    async def list_users(self, limit: int = 100, offset: int = 0) -> list[UserRead]:
        limit = clamp_limit(limit)
        rows = await self._users.get_all(limit=limit, offset=offset)
        return [UserRead.model_validate(u) for u in rows]

    async def get_user_by_id(self, user_id: int) -> UserRead | None:
        row = await self._users.get_by_id(user_id)
        if row is None:
            return None
        return UserRead.model_validate(row)

    async def get_profile(self, user_id: int) -> UserRead:
        row = await self._users.get_by_id(user_id)
        if row is None:
            raise EntityNotFoundError("User", entity_id=user_id)
        return await self._to_profile(row)

    async def update_me(self, user_id: int, data: UserUpdate) -> UserRead:
        values: dict[str, str | None] = {}
        if data.full_name is not None:
            name = data.full_name.strip()
            if not name:
                raise AppException("Name cannot be empty.", status_code=400)
            values["full_name"] = name
        if data.city is not None:
            city = data.city.strip()
            values["city"] = city or None
        if not values:
            return await self.get_profile(user_id)

        updated = await self._users.update(user_id, **values)
        if updated is None:
            raise EntityNotFoundError("User", entity_id=user_id)
        try:
            await self._session.commit()
        except Exception as exc:
            await self._session.rollback()
            raise TransactionFailedError(
                "Failed to update profile; transaction rolled back.",
            ) from exc
        await self._session.refresh(updated)
        return await self._to_profile(updated)

    async def upload_avatar(
        self,
        user_id: int,
        *,
        content: bytes,
        content_type: str,
    ) -> UserRead:
        if self._storage is None:
            raise AppException("Storage is not configured.", status_code=503)
        user = await self._users.get_by_id(user_id)
        if user is None:
            raise EntityNotFoundError("User", entity_id=user_id)

        previous = user.avatar_url
        url = self._storage.save_image(content, content_type)
        user.avatar_url = url
        try:
            await self._session.commit()
        except Exception as exc:
            await self._session.rollback()
            self._storage.delete_file(url)
            raise TransactionFailedError(
                "Failed to save avatar; transaction rolled back.",
            ) from exc
        if previous and previous != url:
            try:
                self._storage.delete_file(previous)
            except Exception:
                pass
        await self._session.refresh(user)
        return await self._to_profile(user)

    async def topup_wallet(self, user_id: int, amount: Decimal) -> UserRead:
        user = await self._users.get_for_update(user_id)
        if user is None:
            raise EntityNotFoundError("User", entity_id=user_id)
        await WalletService(self._session).topup(user, amount)
        return await self._to_profile(user)

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

    async def _to_profile(self, user: User) -> UserRead:
        rating = 0
        reviews_count = 0
        listings_count = 0
        if self._reviews is not None:
            avg, reviews_count = await self._reviews.stats_for_subject(user.id)
            rating = int(round(avg)) if reviews_count else 0
        if self._listings is not None:
            listings_count = await self._listings.count_by_owner(user.id)
        base = UserRead.model_validate(user)
        return base.model_copy(
            update={
                "rating": rating,
                "reviews_count": reviews_count,
                "listings_created_count": listings_count,
            }
        )


class ReviewService:
    def __init__(
        self,
        session: AsyncSession,
        review_repository: ReviewRepository,
        user_repository: UserRepository,
    ) -> None:
        self._session = session
        self._reviews = review_repository
        self._users = user_repository

    @staticmethod
    def _to_read(row: Review) -> ReviewRead:
        author_name = row.author.full_name if row.author is not None else "Пользователь"
        return ReviewRead(
            id=row.id,
            author_id=row.author_id,
            subject_id=row.subject_id,
            author_name=author_name,
            rating=row.rating,
            comment=row.comment,
            owner_reply=row.owner_reply,
            created_at=row.created_at,
        )

    async def list_for_user(
        self,
        subject_id: int,
        *,
        limit: int = 40,
        offset: int = 0,
    ) -> list[ReviewRead]:
        subject = await self._users.get_by_id(subject_id)
        if subject is None:
            raise EntityNotFoundError("User", entity_id=subject_id)
        limit = clamp_limit(limit)
        rows = await self._reviews.list_for_subject(
            subject_id,
            limit=limit,
            offset=offset,
        )
        return [self._to_read(row) for row in rows]

    async def create_review(
        self,
        subject_id: int,
        *,
        author_id: int,
        rating: int,
        comment: str,
    ) -> ReviewRead:
        if author_id == subject_id:
            raise AppException("You cannot review yourself.", status_code=400)
        subject = await self._users.get_by_id(subject_id)
        if subject is None:
            raise EntityNotFoundError("User", entity_id=subject_id)
        existing = await self._reviews.get_by_author_and_subject(
            author_id=author_id,
            subject_id=subject_id,
        )
        if existing is not None:
            raise AppException("You already reviewed this user.", status_code=400)

        created = await self._reviews.create(
            Review(
                author_id=author_id,
                subject_id=subject_id,
                rating=rating,
                comment=comment.strip(),
            )
        )
        try:
            await self._session.commit()
        except Exception as exc:
            await self._session.rollback()
            raise TransactionFailedError(
                "Failed to create review; transaction rolled back.",
            ) from exc
        loaded = await self._reviews.get_by_id_loaded(created.id)
        if loaded is None:
            raise TransactionFailedError("Review vanished after create.")
        return self._to_read(loaded)

    async def reply(
        self,
        review_id: int,
        *,
        current_user_id: int,
        owner_reply: str | None,
    ) -> ReviewRead:
        row = await self._reviews.get_by_id_loaded(review_id)
        if row is None:
            raise EntityNotFoundError("Review", entity_id=review_id)
        if row.subject_id != current_user_id:
            raise OwnershipError("Only the reviewed user can reply.")
        text = (owner_reply or "").strip()
        row.owner_reply = text or None
        try:
            await self._session.commit()
        except Exception as exc:
            await self._session.rollback()
            raise TransactionFailedError(
                "Failed to save review reply; transaction rolled back.",
            ) from exc
        loaded = await self._reviews.get_by_id_loaded(review_id)
        if loaded is None:
            raise TransactionFailedError("Review vanished after reply.")
        return self._to_read(loaded)
