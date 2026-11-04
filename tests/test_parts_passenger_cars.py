"""Parts Step 2 — passenger cars catalog contract."""
from __future__ import annotations

from app.seeds.parts_passenger_cars import (
    PASSENGER_CAR_SECTIONS,
    build_passenger_cars_catalog,
    resolve_passenger_parts_alias,
)


def test_passenger_cars_catalog_shape() -> None:
    cat = build_passenger_cars_catalog()
    assert cat["applicability"] == "passenger_cars"
    assert len(cat["sections"]) == 15
    labels = [s["label"] for s in cat["sections"]]
    assert labels[0] == "Двигатель"
    assert labels[5] == "Кузов и наружные детали"
    assert labels[-1] == "Другое"
    assert "Подшипники" not in labels
    assert "Масла, смазки и технические жидкости" not in labels

    brakes = next(s for s in cat["sections"] if s["value"] == "brakes")
    brake_labels = [i["label"] for i in brakes["items"]]
    assert "Тормозные колодки" in brake_labels
    assert "Передние тормозные колодки" not in brake_labels

    body = next(s for s in cat["sections"] if s["value"] == "body")
    optics = next(i for i in body["items"] if i["value"] == "optics")
    assert [c["label"] for c in optics["children"]] == [
        "Фары",
        "Задние фонари",
        "Противотуманные фары",
        "Поворотники",
        "Лампы",
        "Линзы",
        "Другое",
    ]

    field_keys = [f["field_key"] for f in cat["listing_fields"]]
    assert field_keys == ["brand", "model", "year", "condition", "city"]
    assert "oem_number" not in field_keys
    assert "vehicle_applicability" in cat["path_fields"]


def test_passenger_parts_alias_normalization() -> None:
    assert resolve_passenger_parts_alias("передние колодки") == {
        "part_section": "brakes",
        "part_name": "brake_pads",
    }
    assert resolve_passenger_parts_alias("LED фара") == {
        "part_section": "body",
        "part_name": "optics",
        "part_subtype": "headlights",
    }
    assert resolve_passenger_parts_alias("спортивный глушитель") == {
        "part_section": "exhaust",
        "part_name": "muffler",
    }


def test_passenger_cars_catalog_endpoint() -> None:
    """Live-API smoke (avoids Win/asyncpg TestClient dispose flake)."""
    import json
    import urllib.error
    import urllib.request

    url = "http://127.0.0.1:8000/api/v1/categories/parts/catalog/passenger_cars"
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            status = resp.status
            body = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError) as exc:
        raise AssertionError(f"backend not reachable for passenger catalog: {exc}") from exc

    assert status == 200
    assert len(body["sections"]) == 15
    assert body["sections"][0]["label"] == "Двигатель"
    assert len(PASSENGER_CAR_SECTIONS) == 15

    # Catalog Expansion: moto is a real applicability catalog (not 404).
    moto_url = "http://127.0.0.1:8000/api/v1/categories/parts/catalog/moto"
    with urllib.request.urlopen(moto_url, timeout=5) as moto_resp:
        assert moto_resp.status == 200
        moto_body = json.loads(moto_resp.read().decode("utf-8"))
    assert len(moto_body.get("sections") or []) >= 1

    missing_url = "http://127.0.0.1:8000/api/v1/categories/parts/catalog/not_a_real_applicability"
    try:
        urllib.request.urlopen(missing_url, timeout=5)
        raise AssertionError("expected 404 for unknown catalog")
    except urllib.error.HTTPError as exc:
        assert exc.code == 404


def test_intelligence_682_picker_parent_no_live_schema() -> None:
    """P1 hygiene: Auto Parts parent is picker-only; STEP 1 lives in catalog path_fields."""
    import asyncio

    from sqlalchemy import text

    from app.db.session import async_session_maker, engine
    from app.repositories.category_alias_repository import CategoryAliasRepository
    from app.repositories.category_moderation_rule_repository import (
        CategoryModerationRuleRepository,
    )
    from app.repositories.category_repository import CategoryRepository
    from app.repositories.category_routing_rule_repository import (
        CategoryRoutingRuleRepository,
    )
    from app.repositories.vehicle_repository import VehicleAliasRepository
    from app.services.category_intelligence_service import CategoryIntelligenceService

    cat = build_passenger_cars_catalog()
    assert "vehicle_applicability" in cat["path_fields"]

    async def _run() -> None:
        async with async_session_maker() as session:
            cat_id = int(
                (
                    await session.execute(
                        text(
                            "SELECT id FROM categories WHERE slug='transport-auto-parts'"
                        )
                    )
                ).scalar_one()
            )
            parent_fields = int(
                (
                    await session.execute(
                        text(
                            "SELECT COUNT(*) FROM category_core_fields "
                            "WHERE category_id = :cid"
                        ),
                        {"cid": cat_id},
                    )
                ).scalar_one()
            )
            assert parent_fields == 0
            svc = CategoryIntelligenceService(
                CategoryRepository(session),
                CategoryAliasRepository(session),
                CategoryRoutingRuleRepository(session),
                CategoryModerationRuleRepository(session),
                VehicleAliasRepository(session),
            )
            intel = await svc.get_category_intelligence(cat_id)
            assert intel is not None
            assert not any(
                f.field_key == "vehicle_applicability" for f in intel.core_fields
            )
        await engine.dispose()

    asyncio.run(_run())
