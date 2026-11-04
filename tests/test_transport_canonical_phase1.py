"""Tests for transport catalog canonicalization Phase 1."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from sqlalchemy import text

from app.api.v1.endpoints import listings as listings_endpoint
from app.repositories.category_repository import CategoryRepository
from app.services.category_service import CategoryService
from app.db.base import Base  # noqa: F401 — register ORM mappers
from app.db.session import async_session_maker
from app.seeds.category_data import (
    CATEGORY_ALIASES,
    CORE_FIELDS,
    ROUTING_RULES,
    SEARCH_FILTERS,
    SUBCATEGORIES,
    all_category_slugs,
)
from app.seeds.loader import CategorySeedLoader
from app.seeds.transport_canonical import (
    CANONICAL_MAP_V1_PATH,
    LEGACY_TRANSPORT_IDS,
    PARTS_ALIAS_TO_CANONICAL_SLUG,
    RETIRED_TRANSPORT_SLUGS,
    TRUCKS_ALIAS_TO_CANONICAL_SLUG,
)
from app.seeds.transport_canonical_migration import (
    RETIRED_TRANSPORT_SLUGS_FOR_ROUTING,
    load_canonical_map,
    verify_post_migration,
)
from app.services.category_routing_service import CategoryRoutingService


def test_canonical_map_v1_valid() -> None:
    data = load_canonical_map()
    assert data["version"] == "catalog-canonical-map-v1"
    assert len(data["mappings"]) == 5
    legacy_ids = {m["legacy_id"] for m in data["mappings"]}
    assert legacy_ids == {606, 607, 608, 609, 610}


def test_retired_transport_not_in_subcategories() -> None:
    transport_subs = {s[0] for s in SUBCATEGORIES["transport"]}
    assert not transport_subs
    for slug in RETIRED_TRANSPORT_SLUGS:
        assert slug not in transport_subs


def test_canonical_transport_in_seed_data() -> None:
    slugs = all_category_slugs()
    assert "transport-car-sale" in slugs
    assert "transport-cargo" in slugs
    assert "transport-cars" not in CATEGORY_ALIASES
    assert "transport-car-sale" in CATEGORY_ALIASES
    assert "transport-car-sale" in SEARCH_FILTERS
    assert "transport-cars" not in SEARCH_FILTERS
    assert "transport-car-sale" in CORE_FIELDS
    assert "transport-auto-parts" in CORE_FIELDS
    assert "transport-cargo" in CORE_FIELDS
    assert "transport-special-equipment" in CORE_FIELDS


def test_kamaz_routing_targets_transport_cargo() -> None:
    kamaz = next(r for r in ROUTING_RULES if r[0] == "kamaz_sale")
    assert kamaz[3]["target_category_slug"] == "transport-cargo"
    assert kamaz[3]["target_category_slug"] in all_category_slugs()


def test_parts_alias_split_explicit() -> None:
    assert PARTS_ALIAS_TO_CANONICAL_SLUG["шины"] == "transport-tires-wheels"
    assert PARTS_ALIAS_TO_CANONICAL_SLUG["запчасти"] == "transport-auto-parts"
    tires_aliases = CATEGORY_ALIASES.get("transport-tires-wheels", [])
    parts_aliases = CATEGORY_ALIASES.get("transport-auto-parts", [])
    assert "шины" in tires_aliases
    assert "запчасти" in parts_aliases


def test_trucks_alias_split_explicit() -> None:
    assert TRUCKS_ALIAS_TO_CANONICAL_SLUG["спецтехника"] == "transport-special-equipment"
    assert TRUCKS_ALIAS_TO_CANONICAL_SLUG["камаз"] == "transport-cargo"


def test_routing_service_no_retired_transport_slugs() -> None:
    retired = RETIRED_TRANSPORT_SLUGS_FOR_ROUTING
    for route in CategoryRoutingService._STATIC_ROUTES:
        assert route.category_slug not in retired


def test_canonical_map_file_tracked() -> None:
    assert CANONICAL_MAP_V1_PATH.is_file()
    raw = json.loads(CANONICAL_MAP_V1_PATH.read_text(encoding="utf-8"))
    assert raw["legacy_transport_ids"] == [606, 607, 608, 609, 610]


@pytest.mark.asyncio
async def test_loader_skips_retired_in_upsert() -> None:
    """Retired slug must not be (re)created by _upsert_category."""
    calls: list[str] = []

    async def fake_execute(_stmt):  # noqa: ANN001
        class Result:
            def scalar_one_or_none(self):
                return None

        return Result()

    class FakeSession:
        async def execute(self, stmt):  # noqa: ANN001
            return await fake_execute(stmt)

        def add(self, _obj):  # noqa: ANN001
            calls.append("add")

    loader = CategorySeedLoader(FakeSession())  # type: ignore[arg-type]
    await loader._upsert_category(
        slug="transport-cars",
        name="Legacy",
        entity_type=None,
        sort_order=0,
        parent_id=1,
        hint=None,
    )
    assert calls == []


def test_listings_feed_uses_canonical_car_sale_only() -> None:
    assert listings_endpoint._CAR_SALE_SLUGS == ("transport-car-sale",)
    assert "transport-cars" not in listings_endpoint._CAR_SALE_SLUGS


def test_car_sale_seed_aliases_complete() -> None:
    car_aliases = set(CATEGORY_ALIASES.get("transport-car-sale", []))
    expected = {"авто", "машина", "легковушка", "car", "автомобиль", "седан"}
    assert expected.issubset(car_aliases)


def test_cargo_and_spec_equipment_aliases_in_seed() -> None:
    cargo = set(CATEGORY_ALIASES.get("transport-cargo", []))
    spec = set(CATEGORY_ALIASES.get("transport-special-equipment", []))
    assert {"грузовик", "камаз", "газель", "фура"}.issubset(cargo)
    assert "спецтехника" in spec


@pytest.mark.asyncio
async def test_post_migration_db_invariants() -> None:
    """Single DB session — avoids asyncpg event-loop reuse issues on Windows."""
    async with async_session_maker() as session:
        stats = await verify_post_migration(session)
        assert stats["categories_total"] == 600
        assert stats["categories_active"] == 595
        assert stats["categories_inactive"] == 5
        for legacy_id in LEGACY_TRANSPORT_IDS:
            assert stats[f"legacy_{legacy_id}_active"] is False
        assert stats["legacy_transport_still_active"] == []
        assert stats["car_sale_filters"] == 3
        assert stats["car_sale_aliases"] == 6
        assert stats["car_sale_core"] == 7
        assert stats["car_sale_optional"] == 17
        assert stats["transport_l2_active"] == 16
        assert stats["car_sale_listings"] == 113
        assert stats["kamaz_sale_target"] == "transport-cargo"

        filter_keys = (
            await session.execute(
                text(
                    "SELECT filter_key FROM category_filters WHERE category_id = "
                    "(SELECT id FROM categories WHERE slug = 'transport-car-sale') "
                    "ORDER BY filter_key"
                )
            )
        ).scalars().all()
        assert set(filter_keys) == {"brand", "price", "year"}

        repo = CategoryRepository(session)
        service = CategoryService(repo)
        tree = await service.get_category_tree()
        slugs: set[str] = set()

        def collect(nodes: list) -> None:
            for node in nodes:
                slugs.add(node.slug)
                collect(node.children)

        collect(tree)
        for retired in RETIRED_TRANSPORT_SLUGS:
            assert retired not in slugs
        assert "transport-car-sale" in slugs
        assert "transport-cargo" in slugs

        cat = await repo.get_by_slug("transport-car-sale")
        assert cat is not None
        assert cat.is_active is True

        loader = CategorySeedLoader(session)
        await loader.run()
        await loader.run()
        for legacy_id in LEGACY_TRANSPORT_IDS:
            active = (
                await session.execute(
                    text("SELECT is_active FROM categories WHERE id = :id"),
                    {"id": legacy_id},
                )
            ).scalar_one()
            assert active is False
