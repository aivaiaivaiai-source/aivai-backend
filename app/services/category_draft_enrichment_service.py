"""Apply resolver results to editable draft listings (3C-4)."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.category_resolver.draft_enrichment import (
    can_apply_resolver_enrichment,
    enrichment_category_id,
)
from app.core.config import Settings, get_settings
from app.core.exceptions import EntityNotFoundError, OwnershipError
from app.models.category_selection_enums import CategorySelectionSource
from app.models.enums import ListingStatus
from app.models.listing import Listing
from app.models.listing_category_resolver import ListingCategoryResolverResult
from app.repositories.category_repository import CategoryRepository
from app.repositories.listing_repository import ListingRepository
from app.seeds.transport_canonical import RETIRED_TRANSPORT_SLUGS

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DraftEnrichmentResult:
    applied: bool
    category_id: int | None = None
    reason: str = ""


class CategoryDraftEnrichmentService:
    """
    Draft enrichment — NOT final publication assignment.

    Uses listing update side effects (media enqueue) via repository + session commit.
    """

    def __init__(
        self,
        session: AsyncSession,
        settings: Settings | None = None,
    ) -> None:
        self._session = session
        self._settings = settings or get_settings()
        self._listings = ListingRepository(session)
        self._categories = CategoryRepository(session)

    @property
    def enabled(self) -> bool:
        return bool(
            self._settings.CATEGORY_RESOLVER_ENABLED
            and self._settings.CATEGORY_RESOLVER_DRAFT_ENRICHMENT_ENABLED
        )

    async def try_apply_from_resolver_result(
        self,
        listing: Listing,
        result: ListingCategoryResolverResult,
        *,
        input_fingerprint: str,
        actor_user_id: int,
    ) -> DraftEnrichmentResult:
        if not self.enabled:
            return DraftEnrichmentResult(applied=False, reason="disabled")

        if listing.owner_id != actor_user_id:
            raise OwnershipError("You cannot enrich another user's listing.")

        if not can_apply_resolver_enrichment(
            listing,
            result=result,
            input_fingerprint=input_fingerprint,
        ):
            return DraftEnrichmentResult(applied=False, reason="not_applicable")

        target_id = enrichment_category_id(result)
        if target_id is None:
            return DraftEnrichmentResult(applied=False, reason="no_enrichment_target")

        if listing.category_id == target_id and listing.category_selection_source == CategorySelectionSource.resolver:
            return DraftEnrichmentResult(applied=False, category_id=target_id, reason="already_applied")

        cat = await self._categories.get_by_id(target_id)
        if cat is None or not cat.is_active:
            return DraftEnrichmentResult(applied=False, reason="inactive_category")
        if cat.slug in RETIRED_TRANSPORT_SLUGS:
            return DraftEnrichmentResult(applied=False, reason="retired_category")

        previous_category_id = listing.category_id
        updated = await self._listings.update(
            listing.id,
            category_id=target_id,
            category_selection_source=CategorySelectionSource.resolver,
        )
        if updated is None:
            raise EntityNotFoundError("Listing", entity_id=listing.id)

        category_became_known = previous_category_id is None and target_id is not None
        category_changed = (
            previous_category_id is not None
            and target_id is not None
            and previous_category_id != target_id
        )
        if category_became_known:
            from app.services.media_category_processing import (
                enqueue_category_aware_media_for_listing,
            )

            await enqueue_category_aware_media_for_listing(self._session, listing.id)
        elif category_changed:
            from app.services.media_category_processing import (
                requeue_media_for_category_change,
            )

            await requeue_media_for_category_change(
                self._session,
                listing.id,
                new_category_id=int(target_id),
            )

        logger.info(
            "category_draft_enrichment_applied listing_id=%s category_id=%s status=%s",
            listing.id,
            target_id,
            result.status.value,
        )
        return DraftEnrichmentResult(applied=True, category_id=target_id, reason="applied")
