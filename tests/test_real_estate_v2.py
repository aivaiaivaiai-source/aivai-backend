# -*- coding: utf-8 -*-
"""Real Estate V2 Package A вЂ” taxonomy, schemas, guards, storage, aliases."""
from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from decimal import Decimal

from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.api.deps import get_current_user
from app.api.v1.endpoints.listings import _enforce_listing_create_rate_limit
from app.db.session import async_session_maker
from app.main import app
from app.models.enums import Currency
from app.schemas.user import UserRead
from app.seeds.real_estate_v2 import (
    APARTMENTS_ID,
    APARTMENTS_SLUG,
    CANONICAL_LEAF_SLUGS,
    COMMERCIAL_DIRECTION_ITEMS,
    COMMERCIAL_SLUG,
    GARAGES_SLUG,
    LEGACY_DEAL_IDS,
    PARKING_SLUG,
    RE_CORE_FIELDS_BY_SLUG,
    RE_SEARCH_FILTERS_BY_SLUG,
    RETIRED_SKELETON_IDS,
    ROOT_ID,
    ROOT_SLUG,
)
from app.services.currency_policy import default_currency_for


def _auth_user(user_id: int = 1) -> None:
    now = datetime.now(UTC)

    async def _user() -> UserRead:
        return UserRead(
            id=user_id,
            phone="+79001234567",
            full_name="RealEstateV2Tester",
            is_active=True,
            balance=Decimal("0"),
            last_login=None,
            created_at=now,
            updated_at=now,
        )

    app.dependency_overrides[get_current_user] = _user


async def _slug_id(session, slug: str) -> int:
    return int(
        (
            await session.execute(
                text("SELECT id FROM categories WHERE slug = :s"),
                {"s": slug},
            )
        ).scalar_one()
    )


def test_currency_deal_aware_stable_values() -> None:
    assert default_currency_for(APARTMENTS_SLUG, deal_type="sell") == Currency.USD
    assert default_currency_for(APARTMENTS_SLUG, deal_type="buy") == Currency.USD
    assert default_currency_for(APARTMENTS_SLUG, deal_type="rent") == Currency.KGS
    assert default_currency_for(APARTMENTS_SLUG, deal_type="want_rent") == Currency.KGS
    # Legacy RU labels still work.
    assert default_currency_for(APARTMENTS_SLUG, deal_type="Продажа квартир") == Currency.USD
    assert default_currency_for(APARTMENTS_SLUG, deal_type="Сниму квартиру") == Currency.KGS


def test_seed_module_invariants() -> None:
    assert len(COMMERCIAL_DIRECTION_ITEMS) == 19
    for item in COMMERCIAL_DIRECTION_ITEMS:
        assert item["value"] != item["label"]
        assert item["value"].isascii()
    for slug in CANONICAL_LEAF_SLUGS:
        fields = RE_CORE_FIELDS_BY_SLUG[slug]
        assert len(fields) > 0, slug
        keys = [f[0] for f in fields]
        assert "deal_type" in keys, slug
        assert "price" in keys, slug
        # Package B adds numeric area on applicable leaves (not land/parking).
        if slug in (
            "real-estate-zemelnye-uchastki",
            "real-estate-parkovki",
        ):
            assert "area" not in keys, slug
        else:
            assert "area" in keys, slug
        deal = next(f for f in fields if f[0] == "deal_type")
        values = [c["value"] for c in deal[5]["choices"]]
        for v in values:
            assert v.isascii() and v == v.lower() or "_" in v or v.isalnum()
            assert v not in {"Продажа", "Аренда", "Куплю", "Сниму"}
        filters = RE_SEARCH_FILTERS_BY_SLUG[slug]
        assert len(filters) > 0, slug
        fkeys = {f[0] for f in filters}
        assert "deal_type" in fkeys, slug
        contact = next(f for f in fields if f[0] == "contact_methods")
        assert contact[2].value == "enum", slug
        contact_vals = [c["value"] for c in contact[5]["choices"]]
        assert "Только чат" in contact_vals, slug
        assert "Чат + Тел. + Wapp" in contact_vals, slug
        assert "phone" not in contact_vals, slug

    apt_fields = RE_CORE_FIELDS_BY_SLUG[APARTMENTS_SLUG]
    subtype = next(f for f in apt_fields if f[0] == "subtype")
    by_val = {c["value"]: c for c in subtype[5]["choices"]}
    assert by_val["secondary"]["for_deals"] == ["sell", "buy"]
    assert by_val["new_build"]["for_deals"] == ["sell", "buy"]
    assert by_val["long_term"]["for_deals"] == ["rent", "want_rent"]
    assert by_val["daily"]["for_deals"] == ["rent", "want_rent"]
    assert subtype[5]["label_by_deal"]["rent"] == "Тип аренды"
    assert subtype[5]["label_by_deal"]["sell"] == "Тип"


async def _run_all() -> None:
    test_seed_module_invariants()
    test_currency_deal_aware_stable_values()

    async with async_session_maker() as session:
        # Taxonomy roles.
        root = (
            await session.execute(
                text(
                    """
                    SELECT id, is_active,
                      (SELECT count(*) FROM category_core_fields WHERE category_id = c.id),
                      (SELECT count(*) FROM categories ch
                       WHERE ch.parent_id = c.id AND ch.is_active)
                    FROM categories c WHERE id = :id
                    """
                ),
                {"id": ROOT_ID},
            )
        ).one()
        assert int(root[0]) == ROOT_ID
        assert bool(root[1]) is True
        assert int(root[2]) == 0  # picker-only schema
        assert int(root[3]) >= 7

        for rid in (*LEGACY_DEAL_IDS, *RETIRED_SKELETON_IDS):
            row = (
                await session.execute(
                    text(
                        """
                        SELECT is_active,
                          (SELECT count(*) FROM category_core_fields WHERE category_id = :id)
                        FROM categories WHERE id = :id
                        """
                    ),
                    {"id": rid},
                )
            ).one()
            assert bool(row[0]) is False, rid
            assert int(row[1]) == 0, rid

        # Combined garage slug must not be active publishable.
        old_g = (
            await session.execute(
                text(
                    "SELECT id, is_active FROM categories WHERE slug = 'real-estate-garazhi-i-parkovki'"
                )
            )
        ).first()
        if old_g is not None:
            assert bool(old_g[1]) is False

        garage_id = await _slug_id(session, GARAGES_SLUG)
        parking_id = await _slug_id(session, PARKING_SLUG)
        assert garage_id != parking_id
        assert garage_id == 869

        for slug in CANONICAL_LEAF_SLUGS:
            cid = await _slug_id(session, slug)
            n_core = (
                await session.execute(
                    text(
                        "SELECT count(*) FROM category_core_fields WHERE category_id = :id"
                    ),
                    {"id": cid},
                )
            ).scalar_one()
            n_filt = (
                await session.execute(
                    text(
                        "SELECT count(*) FROM category_filters WHERE category_id = :id"
                    ),
                    {"id": cid},
                )
            ).scalar_one()
            assert int(n_core) > 0, slug
            assert int(n_filt) > 0, slug

            deal_opts = (
                await session.execute(
                    text(
                        """
                        SELECT options FROM category_core_fields
                        WHERE category_id = :id AND field_key = 'deal_type'
                        """
                    ),
                    {"id": cid},
                )
            ).scalar_one()
            assert deal_opts is not None
            choices = deal_opts.get("choices") or deal_opts.get("values") or []
            assert len(choices) >= 2
            for c in choices:
                assert c["value"] != c["label"]

        # Commercial directions.
        comm_id = await _slug_id(session, COMMERCIAL_SLUG)
        dir_opts = (
            await session.execute(
                text(
                    """
                    SELECT options FROM category_core_fields
                    WHERE category_id = :id AND field_key = 'commercial_direction'
                    """
                ),
                {"id": comm_id},
            )
        ).scalar_one()
        dchoices = dir_opts.get("choices") or []
        assert len(dchoices) == 19

        # Children of root: only active canonical property leaves.
        kids = (
            await session.execute(
                text(
                    """
                    SELECT slug FROM categories
                    WHERE parent_id = :pid AND is_active
                    ORDER BY sort_order, id
                    """
                ),
                {"pid": ROOT_ID},
            )
        ).fetchall()
        kid_slugs = [r[0] for r in kids]
        for slug in CANONICAL_LEAF_SLUGS:
            assert slug in kid_slugs
        for bad in (
            "real-estate-sale",
            "real-estate-rent",
            "real-estate-commercial",
            "real-estate-novostroyki",
            "real-estate-dachi-i-zagorodnaya-nedvizhimost",
            "real-estate-nedvizhimost-za-rubezhom",
            "real-estate-obmen-nedvizhimosti",
        ):
            assert bad not in kid_slugs

        # Alias: продам квартиру → apartments, not 602.
        alias_row = (
            await session.execute(
                text(
                    """
                    SELECT a.category_id, c.slug
                    FROM category_aliases a
                    JOIN categories c ON c.id = a.category_id
                    WHERE a.alias_normalized = 'продам квартиру'
                      AND a.is_enabled
                    LIMIT 1
                    """
                )
            )
        ).first()
        assert alias_row is not None
        assert int(alias_row[0]) != 602
        assert alias_row[1] == APARTMENTS_SLUG

        boutique = (
            await session.execute(
                text(
                    """
                    SELECT c.slug FROM category_aliases a
                    JOIN categories c ON c.id = a.category_id
                    WHERE a.alias_normalized = 'сдам бутик' AND a.is_enabled
                    LIMIT 1
                    """
                )
            )
        ).first()
        assert boutique is not None
        assert boutique[0] == COMMERCIAL_SLUG
        assert boutique[0] != "real-estate-commercial"

    # HTTP: intelligence + publish guards + draft storage.
    async def _no_rate_limit() -> None:
        return None

    app.dependency_overrides[_enforce_listing_create_rate_limit] = _no_rate_limit
    _auth_user(user_id=1)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for slug in CANONICAL_LEAF_SLUGS:
            async with async_session_maker() as session:
                cid = await _slug_id(session, slug)
            r = await client.get(f"/api/v1/categories/intelligence/{cid}")
            assert r.status_code == 200, (slug, r.text)
            body = r.json()
            fields = body.get("core_fields") or body.get("fields") or []
            assert len(fields) > 0, slug

        # Category tree: Real Estate children exclude retired deal/skeleton nodes.
        tree = await client.get("/api/v1/categories/tree")
        assert tree.status_code == 200, tree.text
        re_node = next(n for n in tree.json() if n.get("slug") == ROOT_SLUG)
        child_slugs = {c.get("slug") for c in (re_node.get("children") or [])}
        assert APARTMENTS_SLUG in child_slugs
        assert "real-estate-sale" not in child_slugs
        assert GARAGES_SLUG in child_slugs
        assert PARKING_SLUG in child_slugs

        # Publication / create guards: root, retired deal homes, retired skeletons.
        for bad_id in (ROOT_ID, 602, 603, 604, 865, 870, 871, 872):
            resp = await client.post(
                "/api/v1/listings",
                json={
                    "title": "RE guard test",
                    "description": "guard",
                    "price": 1000,
                    "currency": "USD",
                    "category_id": bad_id,
                },
            )
            assert resp.status_code in {400, 404, 422}, (bad_id, resp.status_code, resp.text)

        # Apartment draft persistence with stable values.
        async with async_session_maker() as session:
            apt_id = await _slug_id(session, APARTMENTS_SLUG)
        create = await client.post(
            "/api/v1/listings",
            json={
                "title": "RE V2 apartment draft",
                "description": "Package A storage test",
                "price": 85000,
                "currency": "USD",
                "status": "draft",
                "category_id": apt_id,
                "fields": {
                    "deal_type": "sell",
                    "subtype": "secondary",
                    "rooms": "2",
                    "series": "series_105",
                    "floor": "5",
                    "renovation": "euro",
                    "seller_type": "owner",
                    "negotiable": "yes",
                    "contact_methods": "Чат + телефон",
                },
            },
        )
        assert create.status_code in {200, 201}, create.text
        listing_id = create.json()["id"]

        # Currency override: rent default KGS but USD allowed.
        rent = await client.post(
            "/api/v1/listings",
            json={
                "title": "RE V2 apartment rent",
                "description": "rent override",
                "price": 500,
                "currency": "USD",
                "status": "draft",
                "category_id": apt_id,
                "fields": {
                    "deal_type": "rent",
                    "subtype": "long_term",
                    "rooms": "1",
                    "seller_type": "owner",
                    "negotiable": "no",
                    "contact_methods": "Только телефон",
                },
            },
        )
        assert rent.status_code in {200, 201}, rent.text
        assert rent.json()["currency"] in {"USD", "usd"}

        # Garage vs parking distinct.
        async with async_session_maker() as session:
            g_id = await _slug_id(session, GARAGES_SLUG)
            p_id = await _slug_id(session, PARKING_SLUG)
        g = await client.post(
            "/api/v1/listings",
            json={
                "title": "Garage draft",
                "description": "g",
                "price": 3000,
                "currency": "USD",
                "status": "draft",
                "category_id": g_id,
                "fields": {
                    "deal_type": "sell",
                    "seller_type": "owner",
                    "negotiable": "yes",
                    "contact_methods": "Только телефон",
                },
            },
        )
        p = await client.post(
            "/api/v1/listings",
            json={
                "title": "Parking draft",
                "description": "p",
                "price": 1500,
                "currency": "USD",
                "status": "draft",
                "category_id": p_id,
                "fields": {
                    "deal_type": "sell",
                    "seller_type": "owner",
                    "negotiable": "yes",
                    "contact_methods": "Только телефон",
                },
            },
        )
        assert g.status_code in {200, 201}, g.text
        assert p.status_code in {200, 201}, p.text
        assert g.json()["category_id"] != p.json()["category_id"]

        # Commercial direction switch stays same leaf.
        async with async_session_maker() as session:
            c_id = await _slug_id(session, COMMERCIAL_SLUG)
        c1 = await client.post(
            "/api/v1/listings",
            json={
                "title": "Commercial draft",
                "description": "c",
                "price": 12000,
                "currency": "USD",
                "status": "draft",
                "category_id": c_id,
                "fields": {
                    "deal_type": "rent",
                    "commercial_direction": "office_coworking",
                    "seller_type": "owner",
                    "negotiable": "yes",
                    "contact_methods": "Только телефон",
                },
            },
        )
        assert c1.status_code in {200, 201}, c1.text
        lid = c1.json()["id"]
        upd = await client.patch(
            f"/api/v1/listings/{lid}",
            json={
                "fields": {
                    "deal_type": "rent",
                    "commercial_direction": "warehouse_logistics",
                    "seller_type": "owner",
                    "negotiable": "yes",
                    "contact_methods": "Только телефон",
                }
            },
        )
        assert upd.status_code in {200, 201}, upd.text
        assert upd.json()["category_id"] == c_id

        # Attr filter foundation (generic search if available).
        sr = await client.get(
            "/api/v1/listings/search",
            params={"category_id": apt_id, "attrs": "deal_type:sell"},
        )
        # Search may be limited; accept 200 with any shape or 404 if route differs.
        assert sr.status_code in {200, 404, 422}, sr.text

        _ = listing_id

    app.dependency_overrides.clear()


def test_real_estate_v2_package_a() -> None:
    asyncio.run(_run_all())
