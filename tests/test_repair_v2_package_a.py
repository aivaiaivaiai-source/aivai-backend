"""Repair & Construction V2 Package A — taxonomy + Create SoT."""

from __future__ import annotations

import pytest

from app.seeds.repair_sections_catalog import REPAIR_SECTIONS
from app.seeds.repair_v2 import (
    REPAIR_V2_ALIAS_REMAP,
    REPAIR_V2_CANONICAL_LEAVES,
    REPAIR_V2_CANONICAL_SLUGS,
    REPAIR_V2_GOODS_ALIAS_REMAP,
    REPAIR_V2_RETIRED_SLUGS,
    REPAIR_V2_SECTION_TO_SLUG,
    REPAIR_V2_WORK_ALIAS_REMAP,
    build_repair_v2_core_fields,
)


def test_repair_v2_canonical_shape() -> None:
    assert len(REPAIR_V2_CANONICAL_LEAVES) == 28
    assert len(REPAIR_V2_CANONICAL_SLUGS) == 28
    assert len(REPAIR_SECTIONS) == 28
    assert set(REPAIR_V2_SECTION_TO_SLUG) == set(REPAIR_SECTIONS)
    assert set(REPAIR_V2_SECTION_TO_SLUG.values()) == REPAIR_V2_CANONICAL_SLUGS
    labels = {lab for _s, lab, _o in REPAIR_V2_CANONICAL_LEAVES}
    assert "ЖБИ, сетки и плёнки" in labels
    assert "Стеновые материалы" in labels
    assert "Краски и лаки" in labels
    assert "Плинтусы и декор" in labels
    assert "Крепёж и расходные материалы" in labels
    assert "Строительные материалы" not in labels
    assert REPAIR_V2_RETIRED_SLUGS == {
        "repair-building",
        "construction-work",
        "repair-tools",
    }
    assert REPAIR_V2_GOODS_ALIAS_REMAP["плитка"].startswith("repair-construction-")
    assert REPAIR_V2_WORK_ALIAS_REMAP["ремонт квартиры"].startswith("services-")


def test_repair_v2_catalog_identity_matches_db_slugs() -> None:
    for key, slug in REPAIR_V2_SECTION_TO_SLUG.items():
        assert REPAIR_SECTIONS[key]["category_slug"] == slug
    ceilings = [i["label"] for i in REPAIR_SECTIONS["ceilings"]["roles"]]
    assert "Материалы для натяжных потолков" in ceilings
    assert "Натяжные потолки" not in ceilings


def test_repair_v2_core_fields_seed_shape() -> None:
    cores = build_repair_v2_core_fields()
    assert set(cores) == REPAIR_V2_CANONICAL_SLUGS
    for slug, fields in cores.items():
        keys = [f[0] for f in fields]
        assert keys[0] == "repair_kind"
        assert "price" in keys
        assert "negotiable" in keys
        assert "contact_methods" in keys
        assert "seller_type" in keys
        price = next(f for f in fields if f[0] == "price")
        assert price[1] == "Цена"
        assert price[3] is True  # required goods price
        # No Services «Цена от»
        assert all(f[1] != "Цена от" for f in fields)
        assert all(
            "По договорённости" not in str((f[5] or {}).get("choices", []))
            for f in fields
        )


def test_repair_v2_dependent_moisture_on_lumber() -> None:
    cores = build_repair_v2_core_fields()
    lumber = cores["repair-construction-pilomaterialy"]
    moisture = next(f for f in lumber if f[0] == "moisture")
    opts = moisture[5] or {}
    assert opts["depends_on"]["field"] == "repair_kind"
    assert "Доска" in opts["depends_on"]["values"]


@pytest.mark.asyncio
async def test_repair_v2_db_taxonomy_and_intelligence(client) -> None:
    from sqlalchemy import text

    from app.db.session import async_session_maker

    async with async_session_maker() as s:
        root = (
            await s.execute(
                text(
                    "SELECT id, is_active FROM categories WHERE slug='repair-construction'"
                )
            )
        ).one()
        root_id = int(root[0])
        assert root[1] is True
        active = (
            await s.execute(
                text(
                    """
                    SELECT slug, name FROM categories
                    WHERE parent_id = :pid AND is_active = true
                    ORDER BY sort_order, id
                    """
                ),
                {"pid": root_id},
            )
        ).all()
        assert len(active) == 28
        slugs = {r[0] for r in active}
        assert slugs == REPAIR_V2_CANONICAL_SLUGS
        names = {r[1] for r in active}
        assert "ЖБИ, сетки и плёнки" in names
        assert "Краски и лаки" in names
        assert "Стеновые материалы" in names
        assert "Плинтусы и декор" in names
        for slug in REPAIR_V2_RETIRED_SLUGS:
            row = (
                await s.execute(
                    text(
                        "SELECT is_active FROM categories WHERE slug = :slug"
                    ),
                    {"slug": slug},
                )
            ).one()
            assert row[0] is False
            cores_n = (
                await s.execute(
                    text(
                        """
                        SELECT count(*) FROM category_core_fields cf
                        JOIN categories c ON c.id = cf.category_id
                        WHERE c.slug = :slug
                        """
                    ),
                    {"slug": slug},
                )
            ).scalar_one()
            assert int(cores_n) == 0

        for slug, _label, _sort in REPAIR_V2_CANONICAL_LEAVES:
            n = (
                await s.execute(
                    text(
                        """
                        SELECT count(*) FROM category_core_fields cf
                        JOIN categories c ON c.id = cf.category_id
                        WHERE c.slug = :slug
                        """
                    ),
                    {"slug": slug},
                )
            ).scalar_one()
            assert int(n) > 0, slug

        # Goods aliases
        for alias, target in (
            ("плитка", "repair-construction-plitka-i-keramogranit"),
            ("кровля", "repair-construction-krovlya-i-vodostoki"),
            ("забор", "repair-construction-zabory-vorota-i-ograzhdeniya"),
        ):
            row = (
                await s.execute(
                    text(
                        """
                        SELECT c.slug FROM category_aliases a
                        JOIN categories c ON c.id = a.category_id
                        WHERE a.alias_normalized = :alias AND a.is_enabled
                        """
                    ),
                    {"alias": alias},
                )
            ).one()
            assert row[0] == target

        work = (
            await s.execute(
                text(
                    """
                    SELECT c.slug FROM category_aliases a
                    JOIN categories c ON c.id = a.category_id
                    WHERE a.alias_normalized = 'ремонт квартиры' AND a.is_enabled
                    """
                )
            )
        ).one()
        assert work[0] == "services-stroitelnye-i-remontnye-uslugi"

    # Intelligence non-empty for representatives
    reps = [
        "repair-construction-kirpichi-i-stroitelnye-bloki",
        "repair-construction-lakokrasochnye-materialy",
        "repair-construction-santehnika-i-vodosnabzhenie",
        "repair-construction-elektrika-i-osveschenie",
        "repair-construction-instrumenty",
        "repair-construction-elektroinstrumenty",
        "repair-construction-stroitelnoe-oborudovanie",
        "repair-construction-navesy-i-metallokonstruktsii",
        "repair-construction-spetsodezhda-i-sredstva-zaschity",
    ]
    async with async_session_maker() as s:
        for slug in reps:
            cid = (
                await s.execute(
                    text("SELECT id FROM categories WHERE slug = :slug"),
                    {"slug": slug},
                )
            ).scalar_one()
            resp = await client.get(f"/api/v1/categories/intelligence/{cid}")
            assert resp.status_code == 200, slug
            body = resp.json()
            assert body["default_currency"] == "KGS", slug
            keys = [f["field_key"] for f in body["core_fields"]]
            assert "repair_kind" in keys, slug
            assert "price" in keys, slug
            price = next(f for f in body["core_fields"] if f["field_key"] == "price")
            assert price["label"] == "Цена"
            assert price["is_required"] is True

    # Global counts: tree shows 28 active L2; legacy absent.
    tree = await client.get("/api/v1/categories/tree")
    assert tree.status_code == 200
    roots = tree.json()
    repair = next(r for r in roots if r.get("slug") == "repair-construction")
    children = repair.get("children") or []
    active_children = [c for c in children if c.get("is_active", True)]
    assert len(active_children) == 28
    child_slugs = {c["slug"] for c in active_children}
    assert child_slugs == REPAIR_V2_CANONICAL_SLUGS
    assert "repair-building" not in child_slugs
    assert "construction-work" not in child_slugs
    assert "repair-tools" not in child_slugs
    # Canonical ids preserved (933–960).
    ids = {c["id"] for c in active_children}
    assert ids == set(range(933, 961))
