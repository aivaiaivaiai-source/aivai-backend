from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.review import Review
from app.repositories.base import BaseRepository


class ReviewRepository(BaseRepository[Review]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Review)

    async def list_for_subject(
        self,
        subject_id: int,
        *,
        limit: int = 40,
        offset: int = 0,
    ) -> list[Review]:
        stmt = (
            select(Review)
            .where(Review.subject_id == subject_id)
            .options(selectinload(Review.author))
            .order_by(Review.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_author_and_subject(
        self,
        *,
        author_id: int,
        subject_id: int,
    ) -> Review | None:
        stmt = select(Review).where(
            Review.author_id == author_id,
            Review.subject_id == subject_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_loaded(self, review_id: int) -> Review | None:
        stmt = (
            select(Review)
            .where(Review.id == review_id)
            .options(selectinload(Review.author), selectinload(Review.subject))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def stats_for_subject(self, subject_id: int) -> tuple[float, int]:
        stmt = select(
            func.coalesce(func.avg(Review.rating), 0),
            func.count(Review.id),
        ).where(Review.subject_id == subject_id)
        result = await self._session.execute(stmt)
        avg, count = result.one()
        return float(avg or 0), int(count or 0)
