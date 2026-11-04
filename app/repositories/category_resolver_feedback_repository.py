"""Persist resolver vs user category outcomes for offline analysis."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.listing_category_resolver_feedback import (
    CategoryResolverFeedbackOutcome,
    ListingCategoryResolverFeedback,
)


class CategoryResolverFeedbackRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        row: ListingCategoryResolverFeedback,
    ) -> ListingCategoryResolverFeedback:
        self._session.add(row)
        await self._session.flush()
        return row

    async def record(
        self,
        *,
        listing_id: int,
        suggested_category_id: int | None,
        selected_category_id: int | None,
        outcome: CategoryResolverFeedbackOutcome,
        resolver_result_id: int | None = None,
        resolver_version: str | None = None,
    ) -> ListingCategoryResolverFeedback:
        return await self.create(
            ListingCategoryResolverFeedback(
                listing_id=listing_id,
                resolver_result_id=resolver_result_id,
                suggested_category_id=suggested_category_id,
                selected_category_id=selected_category_id,
                outcome=outcome,
                resolver_version=resolver_version,
            )
        )
