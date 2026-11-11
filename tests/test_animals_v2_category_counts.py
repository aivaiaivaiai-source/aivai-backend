"""Animals V2 — L2 category counts vs unfiltered Search total consistency."""
from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy import select, text

from app.db.session import async_session_maker, engine
from app.models.category import Category
from app.models.enums import Currency, ListingStatus
from app.models.listing import Listing
from app.models.listing_field_value import ListingFieldValue
from app.models.user import User
from app.seeds.animals_v2 import (
    ANIMALS_KIND_KEY,
    ANIMALS_SELLER_KEY,
    ANIMALS_V2_CANONICAL_SLUGS,
    ANIMALS_V2_RETIRED_SLUGS,
)


_REPR = (
    "animals-ovtsy-barany-i-kozy",
    "animals-seno-korma-i-kormovye-dobavki",
    "animals-tovary-aksessuary-dlya-zhivotnyh",
)


@pytest.mark.asyncio
async def test_animals_l2_category_count_matches_unfiltered_search(client) -> None:
    await engine.dispose()
    created_ids: list[int] = []
    try:
        async with async_session_maker() as session:
            owner = (
                await session.execute(select(User).order_by(User.id).limit(1))
            ).scalar_one()
            cats = {}
            for slug in _REPR:
                cats[slug] = (
                    await session.execute(select(Category).where(Category.slug == slug))
                ).scalar_one()

            async def _add(slug: str, title: str, kind: str) -> int:
                listing = Listing(
                    title=title,
                    description=title,
                    price=Decimal("500"),
                    currency=Currency.KGS,
                    status=ListingStatus.active,
                    owner_id=owner.id,
                    category_id=cats[slug].id,
                )
                session.add(listing)
                await session.flush()
                created_ids.append(int(listing.id))
                for key, value in {
                    "city": "Бишкек",
                    "contact_methods": "Только чат",
                    ANIMALS_KIND_KEY: kind,
                    ANIMALS_SELLER_KEY: "Частное лицо",
                }.items():
                    session.add(
                        ListingFieldValue(
                            listing_id=listing.id,
                            field_key=key,
                            value_text=value,
                        )
                    )
                return int(listing.id)

            await _add(_REPR[0], "PKG-B-CNT sheep", "Овцы")
            await _add(_REPR[1], "PKG-B-CNT hay", "Сено")
            await _add(_REPR[2], "PKG-B-CNT collar", "Ошейники")
            await session.commit()
            ids = {slug: cats[slug].id for slug in _REPR}

        # Direct SQL active counts
        async with async_session_maker() as session:
            for slug in _REPR:
                n = (
                    await session.execute(
                        text(
                            """
                            SELECT COUNT(*)::int FROM listings
                            WHERE category_id = :cid AND status = 'active'
                            """
                        ),
                        {"cid": ids[slug]},
                    )
                ).scalar_one()
                assert n >= 1, slug

        # Facet _category must include each L2
        resp = await client.get(
            "/api/v1/listings",
            params={"facets": "_category", "limit": 1},
        )
        assert resp.status_code == 200
        facets = resp.json().get("facets") or {}
        cat_facet = {
            str(i["value"]): int(i["count"])
            for i in facets.get("_category") or []
        }
        for slug in _REPR:
            cid = str(ids[slug])
            assert cat_facet.get(cid, 0) >= 1, slug

            # Unfiltered Search total for same L2 agrees with facet bucket
            s = await client.get(
                "/api/v1/listings",
                params={"category_id": ids[slug], "limit": 1},
            )
            assert s.status_code == 200
            total = int(s.json()["total"])
            assert total == cat_facet[cid], (slug, total, cat_facet[cid])

        # Retired Animals L2 must not be active / counted as Search directions
        async with async_session_maker() as session:
            for slug in sorted(ANIMALS_V2_RETIRED_SLUGS):
                row = (
                    await session.execute(select(Category).where(Category.slug == slug))
                ).scalar_one_or_none()
                if row is None:
                    continue
                assert row.is_active is False
            assert set(_REPR) <= ANIMALS_V2_CANONICAL_SLUGS
    finally:
        if created_ids:
            async with async_session_maker() as session:
                await session.execute(
                    ListingFieldValue.__table__.delete().where(
                        ListingFieldValue.listing_id.in_(created_ids)
                    )
                )
                await session.execute(
                    Listing.__table__.delete().where(Listing.id.in_(created_ids))
                )
                await session.commit()


@pytest.mark.asyncio
async def test_animals_existing_test_listing_2327_count_contract(client) -> None:
    """Samsung repro listing identity — active on canonical sheep L2."""
    await engine.dispose()
    async with async_session_maker() as session:
        row = (
            await session.execute(
                text(
                    """
                    SELECT l.id, l.status::text, l.category_id, c.slug
                    FROM listings l
                    JOIN categories c ON c.id = l.category_id
                    WHERE l.id = 2327
                    """
                )
            )
        ).fetchone()
    if row is None:
        pytest.skip("listing 2327 absent in this DB")
    listing_id, status, cat_id, slug = row
    assert status == "active"
    assert slug == "animals-ovtsy-barany-i-kozy"
    assert slug in ANIMALS_V2_CANONICAL_SLUGS

    resp = await client.get(
        "/api/v1/listings",
        params={"category_id": int(cat_id), "limit": 5},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] >= 1
    assert any(int(i["id"]) == int(listing_id) for i in body["items"])

    facets = await client.get(
        "/api/v1/listings",
        params={"facets": "_category", "limit": 1},
    )
    assert facets.status_code == 200
    cat_facet = {
        str(i["value"]): int(i["count"])
        for i in (facets.json().get("facets") or {}).get("_category") or []
    }
    assert cat_facet.get(str(cat_id), 0) >= 1
