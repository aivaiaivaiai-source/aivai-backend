"""Home & Garden V2 Package B — Search filters, facets, Create↔Search parity."""
from __future__ import annotations

import json
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.db.session import async_session_maker, engine
from app.models.category import Category
from app.models.category_filter import CategoryFilter
from app.models.enums import Currency, ListingStatus
from app.models.listing import Listing
from app.models.listing_field_value import ListingFieldValue
from app.models.user import User
from app.seeds.home_garden_catalog_final import HOME_GARDEN_LEAF_SLUGS
from app.seeds.home_garden_filters import (
    HOME_GARDEN_SEARCH_KEY_ALLOWLIST,
    HOME_GARDEN_SEARCH_KEY_EXCLUDE,
    build_home_garden_search_filters,
    search_filters_for_leaf,
)

_FORBIDDEN = HOME_GARDEN_SEARCH_KEY_EXCLUDE | {
    "model",
    "price",
    "negotiable",
    "contact_methods",
}


def test_all_324_leaves_search_policy() -> None:
    m = build_home_garden_search_filters()
    assert len(m) == len(HOME_GARDEN_LEAF_SLUGS) == 324
    for slug, filters in m.items():
        keys = [k for k, *_ in filters]
        assert "seller_type" in keys, slug
        assert not (_FORBIDDEN & set(keys)), (slug, keys)
        for key in keys:
            assert key in HOME_GARDEN_SEARCH_KEY_ALLOWLIST, (slug, key)
            assert key not in HOME_GARDEN_SEARCH_KEY_EXCLUDE, (slug, key)


def test_representative_leaf_contracts() -> None:
    assert [k for k, *_ in search_filters_for_leaf("home-garden-mebel-dlya-doma-divany")] == [
        "foldable",
        "seller_type",
        "condition",
    ]
    assert [k for k, *_ in search_filters_for_leaf("home-garden-mebel-dlya-doma-matrasy")] == [
        "sleeping_place_size",
        "seller_type",
        "condition",
    ]
    assert [
        k
        for k, *_ in search_filters_for_leaf(
            "home-garden-sadovaya-tehnika-gazonokosilki"
        )
    ] == ["power_type", "self_propelled", "seller_type", "condition"]
    assert [
        k
        for k, *_ in search_filters_for_leaf(
            "home-garden-sazhentsy-i-rassada-plodovye-derevya"
        )
    ] == ["seller_type"]
    assert [
        k
        for k, *_ in search_filters_for_leaf(
            "home-garden-udobreniya-dlya-rasteniy-organicheskie-udobreniya"
        )
    ] == ["form", "seller_type"]
    assert [k for k, *_ in search_filters_for_leaf("home-garden-gazovye-ballony")] == [
        "fill_state",
        "seller_type",
        "condition",
    ]
    assert [
        k for k, *_ in search_filters_for_leaf("home-garden-teplitsy-i-parniki-teplitsy")
    ] == ["seller_type", "condition"]


@pytest.mark.asyncio
async def test_home_garden_search_db_filters_and_parity(client) -> None:
    await engine.dispose()
    expected = build_home_garden_search_filters()
    created: list[int] = []
    async with async_session_maker() as session:
        for slug in (
            "home-garden-mebel-dlya-doma-divany",
            "home-garden-mebel-dlya-doma-matrasy",
            "home-garden-sadovaya-tehnika-gazonokosilki",
            "home-garden-sazhentsy-i-rassada-plodovye-derevya",
            "home-garden-gazovye-ballony",
            "home-garden-udobreniya-dlya-rasteniy-organicheskie-udobreniya",
        ):
            cat = (
                await session.execute(select(Category).where(Category.slug == slug))
            ).scalar_one()
            rows = (
                await session.execute(
                    select(CategoryFilter)
                    .where(CategoryFilter.category_id == cat.id)
                    .order_by(CategoryFilter.sort_order)
                )
            ).scalars().all()
            keys = [r.filter_key for r in rows]
            assert keys == [f[0] for f in expected[slug]], slug
            assert not (_FORBIDDEN & set(keys)), (slug, keys)

        owner = (
            await session.execute(select(User).order_by(User.id.asc()).limit(1))
        ).scalar_one()
        divany = (
            await session.execute(
                select(Category).where(
                    Category.slug == "home-garden-mebel-dlya-doma-divany"
                )
            )
        ).scalar_one()
        kresla = (
            await session.execute(
                select(Category).where(
                    Category.slug == "home-garden-mebel-dlya-doma-kresla"
                )
            )
        ).scalar_one()
        matrasy = (
            await session.execute(
                select(Category).where(
                    Category.slug == "home-garden-mebel-dlya-doma-matrasy"
                )
            )
        ).scalar_one()
        mower = (
            await session.execute(
                select(Category).where(
                    Category.slug == "home-garden-sadovaya-tehnika-gazonokosilki"
                )
            )
        ).scalar_one()
        plant = (
            await session.execute(
                select(Category).where(
                    Category.slug
                    == "home-garden-komnatnye-rasteniya-i-tsvety-orhidei"
                )
            )
        ).scalar_one()
        fert = (
            await session.execute(
                select(Category).where(
                    Category.slug
                    == "home-garden-udobreniya-dlya-rasteniy-organicheskie-udobreniya"
                )
            )
        ).scalar_one()
        gas = (
            await session.execute(
                select(Category).where(Category.slug == "home-garden-gazovye-ballony")
            )
        ).scalar_one()
        repair_tools = (
            await session.execute(
                select(Category).where(
                    Category.slug == "repair-construction-instrumenty"
                )
            )
        ).scalar_one_or_none()

        async def _add(
            *,
            category_id: int,
            title: str,
            city: str,
            fields: dict[str, str],
            price: str = "5000",
        ) -> int:
            listing = Listing(
                title=title,
                description=title,
                price=Decimal(price),
                currency=Currency.KGS,
                status=ListingStatus.active,
                owner_id=owner.id,
                category_id=category_id,
            )
            session.add(listing)
            await session.flush()
            created.append(listing.id)
            payload = {"city": city, "region": "Чуйская область", **fields}
            for key, value in payload.items():
                session.add(
                    ListingFieldValue(
                        listing_id=listing.id,
                        field_key=key,
                        value_text=value,
                    )
                )
            return listing.id

        await _add(
            category_id=divany.id,
            title="HG-B divan foldable yes",
            city="Бишкек",
            fields={
                "foldable": "yes",
                "seller_type": "Частное лицо",
                "condition": "used",
            },
        )
        await _add(
            category_id=divany.id,
            title="HG-B divan foldable no",
            city="Бишкек",
            fields={
                "foldable": "no",
                "seller_type": "Частное лицо",
                "condition": "used",
            },
        )
        await _add(
            category_id=kresla.id,
            title="HG-B kreslo isolation",
            city="Бишкек",
            fields={
                "seller_type": "Частное лицо",
                "condition": "used",
            },
        )
        await _add(
            category_id=matrasy.id,
            title="HG-B mattress euro",
            city="Бишкек",
            fields={
                "sleeping_place_size": "euro",
                "seller_type": "Магазин",
                "condition": "new",
            },
        )
        await _add(
            category_id=mower.id,
            title="HG-B mower petrol self",
            city="Бишкек",
            fields={
                "power_type": "petrol",
                "self_propelled": "yes",
                "seller_type": "Частное лицо",
                "condition": "used",
            },
        )
        await _add(
            category_id=mower.id,
            title="HG-B mower electric no-self",
            city="Ош",
            fields={
                "power_type": "electric",
                "self_propelled": "no",
                "seller_type": "Магазин",
                "condition": "new",
            },
        )
        await _add(
            category_id=plant.id,
            title="HG-B orchid plant",
            city="Бишкек",
            fields={"seller_type": "Частное лицо"},
        )
        await _add(
            category_id=fert.id,
            title="HG-B fert liquid",
            city="Бишкек",
            fields={"form": "liquid", "seller_type": "Магазин"},
        )
        await _add(
            category_id=gas.id,
            title="HG-B gas filled",
            city="Бишкек",
            fields={
                "fill_state": "filled",
                "seller_type": "Компания",
                "condition": "used",
            },
        )
        if repair_tools is not None:
            await _add(
                category_id=repair_tools.id,
                title="HG-B repair tools isolation",
                city="Бишкек",
                fields={"seller_type": "Частное лицо", "condition": "used"},
            )
        await session.commit()
        divany_id = int(divany.id)
        matrasy_id = int(matrasy.id)
        mower_id = int(mower.id)
        plant_id = int(plant.id)
        fert_id = int(fert.id)
        gas_id = int(gas.id)

    try:
        # Divan foldable parity
        resp = await client.get(
            "/api/v1/listings",
            params={
                "category_id": divany_id,
                "attrs": json.dumps({"foldable": "yes"}),
                "limit": 40,
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        titles = {i["title"] for i in body["items"]}
        assert "HG-B divan foldable yes" in titles
        assert "HG-B divan foldable no" not in titles
        assert "HG-B kreslo isolation" not in titles

        resp = await client.get(
            "/api/v1/listings",
            params={
                "category_id": divany_id,
                "attrs": json.dumps({"foldable": "no"}),
                "limit": 40,
            },
        )
        titles = {i["title"] for i in resp.json()["items"]}
        assert "HG-B divan foldable no" in titles
        assert "HG-B divan foldable yes" not in titles

        # Mattress sleeping_place_size
        resp = await client.get(
            "/api/v1/listings",
            params={
                "category_id": matrasy_id,
                "attrs": json.dumps({"sleeping_place_size": "euro"}),
                "limit": 40,
            },
        )
        titles = {i["title"] for i in resp.json()["items"]}
        assert "HG-B mattress euro" in titles

        # Lawnmower same → FOUND, wrong → NOT
        resp = await client.get(
            "/api/v1/listings",
            params={
                "category_id": mower_id,
                "attrs": json.dumps(
                    {"power_type": "petrol", "self_propelled": "yes"}
                ),
                "limit": 40,
            },
        )
        titles = {i["title"] for i in resp.json()["items"]}
        assert "HG-B mower petrol self" in titles
        assert "HG-B mower electric no-self" not in titles

        # Plant seller+geo — no plant_name
        resp = await client.get(
            "/api/v1/listings",
            params={
                "category_id": plant_id,
                "city": "Бишкек",
                "attrs": json.dumps({"seller_type": "Частное лицо"}),
                "limit": 40,
            },
        )
        titles = {i["title"] for i in resp.json()["items"]}
        assert "HG-B orchid plant" in titles

        # Fertilizer form
        resp = await client.get(
            "/api/v1/listings",
            params={
                "category_id": fert_id,
                "attrs": json.dumps({"form": "liquid"}),
                "limit": 40,
            },
        )
        titles = {i["title"] for i in resp.json()["items"]}
        assert "HG-B fert liquid" in titles

        resp = await client.get(
            "/api/v1/listings",
            params={
                "category_id": fert_id,
                "attrs": json.dumps({"form": "granules"}),
                "limit": 40,
            },
        )
        titles = {i["title"] for i in resp.json()["items"]}
        assert "HG-B fert liquid" not in titles

        # Gas fill_state — capacity not search
        resp = await client.get(
            "/api/v1/listings",
            params={
                "category_id": gas_id,
                "attrs": json.dumps({"fill_state": "filled"}),
                "limit": 40,
            },
        )
        titles = {i["title"] for i in resp.json()["items"]}
        assert "HG-B gas filled" in titles

        # Geo parity
        resp = await client.get(
            "/api/v1/listings",
            params={"category_id": mower_id, "city": "Бишкек", "limit": 40},
        )
        titles = {i["title"] for i in resp.json()["items"]}
        assert "HG-B mower petrol self" in titles
        assert "HG-B mower electric no-self" not in titles

        resp = await client.get(
            "/api/v1/listings",
            params={"category_id": mower_id, "city": "Ош", "limit": 40},
        )
        titles = {i["title"] for i in resp.json()["items"]}
        assert "HG-B mower electric no-self" in titles
        assert "HG-B mower petrol self" not in titles

        # Facet self-exclusion + total on one refresh
        resp = await client.get(
            "/api/v1/listings",
            params={
                "category_id": divany_id,
                "attrs": json.dumps({"foldable": "yes"}),
                "facets": "foldable,seller_type,condition",
                "limit": 1,
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body["total"], int)
        fold_facet = {
            str(i["value"]): int(i["count"])
            for i in (body.get("facets") or {}).get("foldable", [])
        }
        # Self-exclusion: selected foldable=yes still exposes sibling option buckets.
        assert "yes" in fold_facet
        assert "no" in fold_facet

        # Intelligence: no forbidden detailed filters on divan
        resp = await client.get(f"/api/v1/categories/intelligence/{divany_id}")
        assert resp.status_code == 200
        fkeys = [f["filter_key"] for f in resp.json()["filters"]]
        assert fkeys == ["foldable", "seller_type", "condition"]
        assert not (_FORBIDDEN & set(fkeys))
    finally:
        async with async_session_maker() as session:
            for lid in created:
                listing = await session.get(Listing, lid)
                if listing is not None:
                    await session.delete(listing)
            await session.commit()
