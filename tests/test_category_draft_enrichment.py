"""Substage 3C-4 — draft category enrichment policy tests."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.category_resolver.draft_enrichment import (
    can_apply_resolver_enrichment,
    enrichment_category_id,
)
from app.models.category_resolver_enums import CategoryResolverStatus
from app.models.category_selection_enums import CategorySelectionSource
from app.models.enums import ListingStatus


def _listing(
    *,
    category_id: int | None = None,
    source: CategorySelectionSource | None = None,
    status: ListingStatus = ListingStatus.draft,
) -> SimpleNamespace:
    return SimpleNamespace(
        status=status,
        category_id=category_id,
        category_selection_source=source,
    )


def _result(
    *,
    status: CategoryResolverStatus,
    suggested_id: int | None,
    path: list[dict] | None = None,
    alternatives: list[dict] | None = None,
    fingerprint: str = "fp-1",
) -> SimpleNamespace:
    return SimpleNamespace(
        status=status,
        suggested_category_id=suggested_id,
        candidate_path_json=path or [],
        alternatives_json=alternatives or [],
        input_fingerprint=fingerprint,
    )


def test_enrichment_suggested_uses_suggested_category_id() -> None:
    row = _result(
        status=CategoryResolverStatus.suggested,
        suggested_id=681,
    )
    assert enrichment_category_id(row) == 681


def test_enrichment_ambiguous_drops_to_parent_on_low_margin() -> None:
    row = _result(
        status=CategoryResolverStatus.ambiguous,
        suggested_id=999,
        path=[
            {"id": 605, "slug": "transport", "name": "Транспорт"},
            {"id": 700, "slug": "transport-special", "name": "Спецтехника"},
            {"id": 999, "slug": "transport-special-excavators", "name": "Экскаваторы"},
        ],
        alternatives=[
            {"slug": "transport-special-excavators", "score": 0.52},
            {"slug": "transport-special-other", "score": 0.50},
        ],
    )
    assert enrichment_category_id(row) == 700


def test_enrichment_no_match_returns_none() -> None:
    row = _result(status=CategoryResolverStatus.no_match, suggested_id=None)
    assert enrichment_category_id(row) is None


def test_can_apply_when_draft_has_no_category() -> None:
    listing = _listing(category_id=None, source=None)
    row = _result(status=CategoryResolverStatus.suggested, suggested_id=681)
    assert can_apply_resolver_enrichment(listing, result=row, input_fingerprint="fp-1")


def test_can_apply_when_previous_resolver_selection() -> None:
    listing = _listing(
        category_id=681,
        source=CategorySelectionSource.resolver,
    )
    row = _result(status=CategoryResolverStatus.suggested, suggested_id=691)
    assert can_apply_resolver_enrichment(listing, result=row, input_fingerprint="fp-1")


def test_manual_selection_blocks_enrichment() -> None:
    listing = _listing(
        category_id=681,
        source=CategorySelectionSource.manual,
    )
    row = _result(status=CategoryResolverStatus.suggested, suggested_id=691)
    assert not can_apply_resolver_enrichment(listing, result=row, input_fingerprint="fp-1")


def test_stale_fingerprint_blocks_enrichment() -> None:
    listing = _listing(category_id=None, source=None)
    row = _result(status=CategoryResolverStatus.suggested, suggested_id=681)
    assert not can_apply_resolver_enrichment(listing, result=row, input_fingerprint="fp-2")


def test_l4_path_enrichment_uses_deepest_when_suggested() -> None:
    """Synthetic L4 catalog node is accepted when resolver is confident."""
    row = _result(
        status=CategoryResolverStatus.suggested,
        suggested_id=4044,
        path=[
            {"id": 1, "slug": "l1", "name": "L1"},
            {"id": 2, "slug": "l2", "name": "L2"},
            {"id": 3, "slug": "l3", "name": "L3"},
            {"id": 4044, "slug": "l4-tracked", "name": "L4 Tracked"},
        ],
    )
    assert enrichment_category_id(row) == 4044
