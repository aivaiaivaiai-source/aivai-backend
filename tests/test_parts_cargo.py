"""Parts Step 3 — cargo catalog + regressions."""
from __future__ import annotations

from app.seeds.parts_cargo import (
    CARGO_SECTIONS,
    build_cargo_catalog,
    decode_parts_draft_path,
    encode_parts_draft_path,
    resolve_cargo_parts_alias,
)
from app.seeds.parts_passenger_cars import build_passenger_cars_catalog


def test_cargo_catalog_thirteen_sections() -> None:
    cat = build_cargo_catalog()
    assert cat["applicability"] == "cargo"
    assert len(cat["sections"]) == 15
    assert len(CARGO_SECTIONS) == 15
    labels = [s["label"] for s in cat["sections"]]
    assert labels == [
        "Двигатель",
        "Коробка передач и трансмиссия",
        "Ходовая и подвеска",
        "Рулевое управление",
        "Тормозная система",
        "Кабина и кузов",
        "Электрика и электроника",
        "Печка и кондиционер",
        "Система охлаждения",
        "Топливная система",
        "Выхлопная система",
        "Грузовая часть",
        "Фильтры",
        "Трубки, патрубки и шланги",
        "Другое",
    ]
    assert "Салон" not in labels
    assert "Подшипники" not in labels


def test_cargo_details_and_no_over_split() -> None:
    cat = build_cargo_catalog()
    brakes = next(s for s in cat["sections"] if s["value"] == "brakes")
    assert "Тормозные колодки" in [i["label"] for i in brakes["items"]]
    assert "Передние тормозные колодки" not in [i["label"] for i in brakes["items"]]

    steering = next(s for s in cat["sections"] if s["value"] == "steering")
    assert "Рулевой редуктор" in [i["label"] for i in steering["items"]]

    cabin = next(s for s in cat["sections"] if s["value"] == "cabin_body")
    optics = next(i for i in cabin["items"] if i["value"] == "optics")
    assert [c["label"] for c in optics["children"]][0] == "Фары"

    cargo_area = next(s for s in cat["sections"] if s["value"] == "cargo_area")
    assert "Гидроборт" in [i["label"] for i in cargo_area["items"]]
    assert "Левый борт" not in [i["label"] for i in cargo_area["items"]]

    electrical = next(s for s in cat["sections"] if s["value"] == "electrical")
    elabels = [i["label"] for i in electrical["items"]]
    assert "Генератор" not in elabels
    assert "Стартер" not in elabels


def test_cargo_listing_fields_year_required() -> None:
    cat = build_cargo_catalog()
    fields = {f["field_key"]: f for f in cat["listing_fields"]}
    assert list(fields) == ["brand", "model", "year", "condition", "city"]
    assert fields["year"]["is_required"] is True
    assert "oem_number" not in fields


def test_cargo_alias_and_draft_roundtrip() -> None:
    assert resolve_cargo_parts_alias("гидроборт") == {
        "part_section": "cargo_area",
        "part_name": "tail_lift",
    }
    draft = encode_parts_draft_path(
        applicability="cargo",
        part_section="brakes",
        part_name="brake_pads",
        brand="КамАЗ",
        model="65115",
        year="2018",
        condition="used",
        city="Бишкек",
    )
    restored = decode_parts_draft_path(draft)
    assert restored == draft
    assert "vehicle_applicability" in restored
    assert restored["year"] == "2018"


def test_cargo_catalog_endpoint() -> None:
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    resp = client.get("/api/v1/categories/parts/catalog/cargo")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert len(body["sections"]) == 15
    assert body["listing_fields"][2]["field_key"] == "year"
    assert body["listing_fields"][2]["is_required"] is True


def test_passenger_cars_catalog_regression() -> None:
    cat = build_passenger_cars_catalog()
    assert len(cat["sections"]) == 15
    assert cat["listing_fields"][2]["is_required"] is False
    year = next(f for f in cat["listing_fields"] if f["field_key"] == "year")
    assert year["is_required"] is False


def test_step1_and_car_sale_regression() -> None:
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
    from app.seeds.transport_v2_1 import PARTS_VEHICLE_APPLICABILITY_OPTIONS
    from app.services.category_intelligence_service import CategoryIntelligenceService

    async def _run() -> None:
        async with async_session_maker() as session:
            parts_id = int(
                (
                    await session.execute(
                        text(
                            "SELECT id FROM categories WHERE slug='transport-auto-parts'"
                        )
                    )
                ).scalar_one()
            )
            car_sale = (
                await session.execute(
                    text(
                        """
                        SELECT is_active,
                          (SELECT COUNT(*) FROM listings
                           WHERE category_id = categories.id AND status='active') AS n
                        FROM categories WHERE slug='transport-car-sale'
                        """
                    )
                )
            ).mappings().one()
            assert car_sale["is_active"] is True
            assert int(car_sale["n"]) >= 1

            svc = CategoryIntelligenceService(
                CategoryRepository(session),
                CategoryAliasRepository(session),
                CategoryRoutingRuleRepository(session),
                CategoryModerationRuleRepository(session),
                VehicleAliasRepository(session),
            )
            intel = await svc.get_category_intelligence(parts_id)
            assert intel is not None
            field = next(
                f for f in intel.core_fields if f.field_key == "vehicle_applicability"
            )
            values = [v["value"] for v in (field.options or {}).get("values") or []]
            assert values == [v for v, _ in PARTS_VEHICLE_APPLICABILITY_OPTIONS]
            assert "cargo" in values
        await engine.dispose()

    asyncio.run(_run())
