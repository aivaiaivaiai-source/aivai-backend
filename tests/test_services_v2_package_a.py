# -*- coding: utf-8 -*-
"""Services V2 Package A — taxonomy + Create SoT + price contract."""
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.db.session import async_session_maker, engine
from app.main import app
from app.models.category import Category
from app.models.category_field import CategoryCoreField
from app.models.category_enums import CategoryFieldType
from app.models.listing import Listing
from app.seeds.services_v2 import (
    SERVICES_NEGOTIATED_VALUE,
    SERVICES_V2_CANONICAL_LEAVES,
    SERVICES_V2_CANONICAL_SLUGS,
    SERVICES_V2_RETIRED_SLUGS,
    build_services_v2_catalogs,
    build_services_v2_core_fields,
)


def test_services_v2_merged_kinds_no_dupes() -> None:
    cats = build_services_v2_catalogs()
    cleaning = cats["services-uborka-i-klining"]["kinds"]
    assert "Уборка помещений" in cleaning
    assert "Химчистка одежды и текстиля" in cleaning
    assert "Дезинфекция" in cleaning
    assert len(cleaning) == len(set(cleaning))

    household = cats["services-bytovye-uslugi"]["kinds"]
    assert "Вскрытие дверных замков" in household
    assert "Пошив одежды" in household
    assert len(household) == len(set(household))

    repair = cats["services-remont-tehniki"]["kinds"]
    assert "Установка и подключение бытовой техники" in repair
    assert len(repair) == len(set(repair))

    marketing = cats["services-reklama-i-marketing"]["kinds"]
    assert "Печать полиграфии" in marketing
    assert len(marketing) == len(set(marketing))

    other = cats["services-prochie-uslugi"]["kinds"]
    assert "Риелторские услуги" not in other
    assert len(cats) == 31


def test_services_v2_core_fields_seed_shape() -> None:
    fields = build_services_v2_core_fields()
    assert set(fields) == SERVICES_V2_CANONICAL_SLUGS
    for slug, _label, _sort in SERVICES_V2_CANONICAL_LEAVES:
        keys = [f[0] for f in fields[slug]]
        assert keys[0] == "service_kind"
        assert "executor" in keys
        assert "price" in keys
        assert "negotiable" in keys
        assert "contact_methods" in keys
        assert "service_materials" not in keys
        by_key = {f[0]: f for f in fields[slug]}
        assert by_key["service_kind"][3] is True
        assert by_key["executor"][3] is True
        assert by_key["price"][3] is False
        assert by_key["price"][1] == "Цена от"
        assert by_key["negotiable"][3] is False
        assert by_key["negotiable"][1] == "По договорённости"
        assert by_key["contact_methods"][3] is True
        neg_opts = by_key["negotiable"][5]
        assert neg_opts is not None
        assert any(
            c.get("value") == SERVICES_NEGOTIATED_VALUE
            for c in neg_opts.get("choices", [])
        )
    plumbing = fields["services-santehnika"]
    by_key = {f[0]: f for f in plumbing}
    assert "service_object" in by_key
    assert by_key["service_object"][2] == CategoryFieldType.multi_select
    assert "service_materials" not in by_key


@pytest.mark.asyncio
async def test_services_v2_db_taxonomy_and_intelligence() -> None:
    await engine.dispose()
    async with async_session_maker() as session:
        root = (
            await session.execute(select(Category).where(Category.slug == "services"))
        ).scalar_one()
        assert root.is_active is True
        children = (
            await session.execute(
                select(Category).where(
                    Category.parent_id == root.id,
                    Category.is_active.is_(True),
                )
            )
        ).scalars().all()
        assert len(children) == 31
        by_slug = {c.slug: c for c in children}
        assert set(by_slug) == SERVICES_V2_CANONICAL_SLUGS
        assert by_slug["services-uborka-i-klining"].name == "Клининг"
        assert by_slug["services-kompyutery-i-it-uslugi"].name == "IT-услуги"
        assert by_slug["services-rieltorskie-uslugi"].name == "Риелторские услуги"

        for slug in sorted(SERVICES_V2_RETIRED_SLUGS):
            row = (
                await session.execute(select(Category).where(Category.slug == slug))
            ).scalar_one_or_none()
            if row is None:
                continue
            assert row.is_active is False

        legacy_row = (
            await session.execute(
                select(Category).where(Category.slug == "services-transport")
            )
        ).scalar_one_or_none()
        if legacy_row is not None:
            assert legacy_row.is_active is False
            drafts = (
                await session.execute(
                    select(Listing).where(Listing.category_id == legacy_row.id)
                )
            ).scalars().all()
            for d in drafts:
                assert d.category_id == legacy_row.id

        expected = build_services_v2_core_fields()
        for slug in (
            "services-santehnika",
            "services-uborka-i-klining",
            "services-rieltorskie-uslugi",
            "services-kompyutery-i-it-uslugi",
        ):
            cat = by_slug[slug]
            rows = (
                await session.execute(
                    select(CategoryCoreField)
                    .where(CategoryCoreField.category_id == cat.id)
                    .order_by(CategoryCoreField.sort_order)
                )
            ).scalars().all()
            assert [r.field_key for r in rows] == [f[0] for f in expected[slug]]
            assert "service_materials" not in {r.field_key for r in rows}
            price = next(r for r in rows if r.field_key == "price")
            assert price.label == "Цена от"
            assert price.is_required is False
            negotiable = next(r for r in rows if r.field_key == "negotiable")
            assert negotiable.label == "По договорённости"
            if slug == "services-santehnika":
                obj = next(r for r in rows if r.field_key == "service_object")
                assert obj.field_type == CategoryFieldType.multi_select

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        async with async_session_maker() as session:
            for slug in (
                "services-santehnika",
                "services-uborka-i-klining",
                "services-kompyutery-i-it-uslugi",
                "services-yuridicheskie-uslugi",
                "services-rieltorskie-uslugi",
                "services-uslugi-spetstehniki",
                "services-domashniy-personal",
            ):
                cat = (
                    await session.execute(
                        select(Category).where(Category.slug == slug)
                    )
                ).scalar_one()
                resp = await client.get(
                    f"/api/v1/categories/intelligence/{cat.id}"
                )
                assert resp.status_code == 200, slug
                body = resp.json()
                assert body["default_currency"] == "KGS", slug
                keys = [f["field_key"] for f in body["core_fields"]]
                assert "service_kind" in keys, slug
                assert "executor" in keys, slug
                assert "price" in keys, slug
                assert "negotiable" in keys, slug
                assert "contact_methods" in keys, slug
                assert "service_materials" not in keys, slug
                assert "city" not in keys, slug
                by_key = {f["field_key"]: f for f in body["core_fields"]}
                assert by_key["price"]["label"] == "Цена от", slug
                assert by_key["price"]["is_required"] is False, slug
                assert by_key["negotiable"]["label"] == "По договорённости", slug
                if slug == "services-santehnika":
                    assert by_key["service_object"]["field_type"] == "multi_select"
