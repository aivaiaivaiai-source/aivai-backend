"""Draft category enrichment policy — separate from auto-assign / publication."""

from __future__ import annotations

from app.category_resolver.constants import AMBIGUITY_MARGIN
from app.models.category_resolver_enums import CategoryResolverStatus
from app.models.enums import ListingStatus
from app.models.listing import Listing
from app.models.listing_category_resolver import ListingCategoryResolverResult
from app.models.category_selection_enums import CategorySelectionSource

_APPLICABLE_STATUSES = frozenset(
    {
        CategoryResolverStatus.suggested,
        CategoryResolverStatus.ambiguous,
    }
)


def enrichment_category_id(result: ListingCategoryResolverResult) -> int | None:
    """
    Map resolver result → draft-safe category id.

    ambiguous: prefer defensible ancestor when top candidates are too close.
    """
    if result.status not in _APPLICABLE_STATUSES:
        return None
    if result.suggested_category_id is None:
        return None

    if result.status == CategoryResolverStatus.suggested:
        return result.suggested_category_id

    path = list(result.candidate_path_json or [])
    if not path:
        return result.suggested_category_id

    alts = list(result.alternatives_json or [])
    margin = 1.0
    if len(alts) >= 2:
        try:
            margin = float(alts[0].get("score", 0)) - float(alts[1].get("score", 0))
        except (TypeError, ValueError):
            margin = 0.0

    if margin < AMBIGUITY_MARGIN and len(path) >= 2:
        parent = path[-2]
        parent_id = parent.get("id") if isinstance(parent, dict) else None
        if isinstance(parent_id, int):
            return parent_id

    return result.suggested_category_id


def can_apply_resolver_enrichment(
    listing: Listing,
    *,
    result: ListingCategoryResolverResult,
    input_fingerprint: str,
) -> bool:
    """Human/manual selection always wins over late resolver results."""
    if listing.status != ListingStatus.draft:
        return False
    if result.status == CategoryResolverStatus.stale:
        return False
    if result.input_fingerprint != input_fingerprint:
        return False
    if enrichment_category_id(result) is None:
        return False

    if listing.category_id is None:
        return True

    source = listing.category_selection_source
    if source == CategorySelectionSource.resolver:
        return True

    return False
