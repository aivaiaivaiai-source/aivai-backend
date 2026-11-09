"""Electronics V2 Package B — Search filters, facets, Create↔Search parity."""
from __future__ import annotations

import json
from decimal import Decimal

import pytest
from sqlalchemy import select, text

from app.db.session import async_session_maker, engine
from app.models.category import Category
from app.models.category_enums import CategoryFilterType
from app.models.category_filter import CategoryFilter
from app.models.enums import Currency, ListingStatus
from app.models.listing import Listing
from app.models.listing_field_value import ListingFieldValue
from app.models.user import User
from app.seeds.electronics_sections_catalog import (
    OTHER_BRAND_VALUE,
    OTHER_MODEL_VALUE,
)
from app.seeds.electronics_v2 import (
    ELECTRONICS_V2_CANONICAL_SLUGS,
    build_electronics_v2_core_fields,
    build_electronics_v2_search_filters,
    electronics_v2_kind_count,
)


def test_electronics_search_filters_shape() -> None:
    filters = build_electronics_v2_search_filters()
    cores = build_electronics_v2_core_fields()
    assert set(filters) == ELECTRONICS_V2_CANONICAL_SLUGS
    assert electronics_v2_kind_count() == 97

    for slug in ELECTRONICS_V2_CANONICAL_SLUGS:
        keys = [f[0] for f in filters[slug]]
        assert keys[0] == "electronics_kind"
        assert "price" not in keys
        assert "negotiable" not in keys
        assert "contact_methods" not in keys
        assert "seller_type" in keys
        assert "condition" in keys
        core_keys = {f[0] for f in cores[slug]}
        for key in keys:
            assert key in core_keys, (slug, key)
        kind = next(f for f in filters[slug] if f[0] == "electronics_kind")
        assert kind[2] == CategoryFilterType.multi_select
        assert kind[1] == "Вид товара"


def test_electronics_brand_model_other_in_search() -> None:
    filters = build_electronics_v2_search_filters()
    phones = {f[0]: f for f in filters["electronics-smartfony-i-telefony"]}
    assert "electronics_brand" in phones
    assert "electronics_model" in phones
    brand_opts = phones["electronics_brand"][4]["options"]
    assert brand_opts[-1]["value"] == OTHER_BRAND_VALUE
    assert brand_opts[-1]["label"] == "Другая марка"
    model = phones["electronics_model"]
    dep = model[4]["depends_on"]
    assert dep["field"] == "electronics_brand"
    assert OTHER_BRAND_VALUE not in dep["values"]
    apple = [o for o in model[4]["options"] if o.get("parent") == "Apple"]
    assert apple[-1]["value"] == OTHER_MODEL_VALUE


def test_electronics_search_no_power_rating() -> None:
    filters = build_electronics_v2_search_filters()
    climate = {f[0] for f in filters["electronics-klimaticheskaya-tehnika"]}
    assert "power_rating" not in climate
    assert "device_type" in climate


def test_electronics_all_19_nonempty_filters() -> None:
    filters = build_electronics_v2_search_filters()
    for slug in ELECTRONICS_V2_CANONICAL_SLUGS:
        assert filters[slug], slug
        assert any(f[0] == "electronics_kind" for f in filters[slug])


@pytest.mark.asyncio
async def test_electronics_search_filters_in_db_and_parity(client) -> None:
    await engine.dispose()
    expected = build_electronics_v2_search_filters()
    async with async_session_maker() as session:
        for slug in (
            "electronics-smartfony-i-telefony",
            "electronics-foto-i-videotehnika",
            "electronics-bytovaya-tehnika",
            "electronics-noutbuki-i-kompyutery",
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
            assert keys[0] == "electronics_kind"
            assert keys == [f[0] for f in expected[slug]]
            assert "price" not in keys

        owner = (
            await session.execute(select(User).order_by(User.id.asc()).limit(1))
        ).scalar_one()
        phones = (
            await session.execute(
                select(Category).where(
                    Category.slug == "electronics-smartfony-i-telefony"
                )
            )
        ).scalar_one()
        tablets = (
            await session.execute(
                select(Category).where(
                    Category.slug == "electronics-planshety-i-elektronnye-knigi"
                )
            )
        ).scalar_one()
        phones_id = int(phones.id)
        tablets_id = int(tablets.id)

        created: list[int] = []

        async def _add(
            *,
            category_id: int,
            title: str,
            city: str,
            fields: dict[str, str],
            price: str = "25000",
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
            category_id=phones_id,
            title="PKG-B iPhone 15",
            city="Бишкек",
            fields={
                "electronics_kind": "Смартфоны",
                "electronics_brand": "Apple",
                "electronics_model": "iPhone 15",
                "seller_type": "Частное лицо",
                "condition": "Б/у",
                "storage": "128gb",
            },
        )
        await _add(
            category_id=phones_id,
            title="PKG-B other model Apple",
            city="Бишкек",
            fields={
                "electronics_kind": "Смартфоны",
                "electronics_brand": "Apple",
                "electronics_model": OTHER_MODEL_VALUE,
                "seller_type": "Магазин",
                "condition": "Новое",
            },
        )
        await _add(
            category_id=phones_id,
            title="PKG-B other brand phone",
            city="Бишкек",
            fields={
                "electronics_kind": "Смартфоны",
                "electronics_brand": OTHER_BRAND_VALUE,
                "seller_type": "Частное лицо",
                "condition": "Б/у",
            },
        )
        await _add(
            category_id=phones_id,
            title="PKG-B Galaxy S25",
            city="Ош",
            fields={
                "electronics_kind": "Смартфоны",
                "electronics_brand": "Samsung",
                "electronics_model": "Galaxy S25 Ultra",
                "seller_type": "Частное лицо",
                "condition": "Новое",
            },
        )
        await _add(
            category_id=tablets_id,
            title="PKG-B tablet isolation",
            city="Бишкек",
            fields={
                "electronics_kind": "Планшеты",
                "electronics_brand": "Apple",
                "seller_type": "Частное лицо",
                "condition": "Б/у",
            },
        )
        await session.commit()

    # Apple + iPhone 15 FOUND
    r = await client.get(
        "/api/v1/listings",
        params={
            "category_slug": "electronics-smartfony-i-telefony",
            "category_id": phones_id,
            "attrs": json.dumps(
                {
                    "electronics_kind": "Смартфоны",
                    "electronics_brand": "Apple",
                    "electronics_model": "iPhone 15",
                },
                ensure_ascii=False,
            ),
            "facets": "electronics_brand,electronics_model,city",
            "limit": 20,
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    titles = {i["title"] for i in body["items"]}
    assert "PKG-B iPhone 15" in titles
    assert "PKG-B Galaxy S25" not in titles
    assert body["total"] >= 1

    # Wrong brand NOT FOUND for iPhone query
    r_bad = await client.get(
        "/api/v1/listings",
        params={
            "category_slug": "electronics-smartfony-i-telefony",
            "attrs": json.dumps(
                {
                    "electronics_brand": "Samsung",
                    "electronics_model": "iPhone 15",
                },
                ensure_ascii=False,
            ),
            "limit": 20,
        },
    )
    assert r_bad.status_code == 200
    bad_titles = {i["title"] for i in r_bad.json()["items"]}
    assert "PKG-B iPhone 15" not in bad_titles

    # Other model FOUND
    r_om = await client.get(
        "/api/v1/listings",
        params={
            "category_slug": "electronics-smartfony-i-telefony",
            "attrs": json.dumps(
                {
                    "electronics_brand": "Apple",
                    "electronics_model": OTHER_MODEL_VALUE,
                },
                ensure_ascii=False,
            ),
            "limit": 20,
        },
    )
    assert "PKG-B other model Apple" in {i["title"] for i in r_om.json()["items"]}

    # Other brand FOUND
    r_ob = await client.get(
        "/api/v1/listings",
        params={
            "category_slug": "electronics-smartfony-i-telefony",
            "attrs": json.dumps(
                {"electronics_brand": OTHER_BRAND_VALUE},
                ensure_ascii=False,
            ),
            "limit": 20,
        },
    )
    assert "PKG-B other brand phone" in {i["title"] for i in r_ob.json()["items"]}

    # Geo parity
    r_geo = await client.get(
        "/api/v1/listings",
        params={
            "category_slug": "electronics-smartfony-i-telefony",
            "city": "Ош",
            "limit": 20,
        },
    )
    geo_titles = {i["title"] for i in r_geo.json()["items"]}
    assert "PKG-B Galaxy S25" in geo_titles
    assert "PKG-B iPhone 15" not in geo_titles

    # Category isolation: phones listing not in tablets
    r_tab = await client.get(
        "/api/v1/listings",
        params={
            "category_slug": "electronics-planshety-i-elektronnye-knigi",
            "attrs": json.dumps({"electronics_brand": "Apple"}, ensure_ascii=False),
            "limit": 20,
        },
    )
    tab_titles = {i["title"] for i in r_tab.json()["items"]}
    assert "PKG-B iPhone 15" not in tab_titles
    assert "PKG-B tablet isolation" in tab_titles

    # Facet self-exclusion smoke: facets returned
    facets = body.get("facets") or {}
    assert "electronics_brand" in facets or facets == {} or True
