"""Vehicle brand/model catalogs scoped by vehicle_type / parts applicability."""
from __future__ import annotations

import asyncio

from sqlalchemy import text

from app.core.exceptions import EntityNotFoundError
from app.db.session import async_session_maker, engine
from app.models.category_enums import VehicleType
from app.repositories.category_alias_repository import CategoryAliasRepository
from app.repositories.category_moderation_rule_repository import (
    CategoryModerationRuleRepository,
)
from app.repositories.category_repository import CategoryRepository
from app.repositories.category_routing_rule_repository import (
    CategoryRoutingRuleRepository,
)
from app.repositories.vehicle_repository import (
    VehicleAliasRepository,
    VehicleBrandRepository,
    VehicleModelRepository,
)
from app.seeds.parts_cargo import decode_parts_draft_path, encode_parts_draft_path
from app.seeds.transport_v2_1 import PARTS_VEHICLE_APPLICABILITY_OPTIONS
from app.services.category_intelligence_service import CategoryIntelligenceService
from app.services.parts_vehicle_type import (
    PARTS_APPLICABILITY_TO_VEHICLE_TYPE,
    resolve_catalog_vehicle_type,
)
from app.services.vehicle_catalog_service import VehicleCatalogService


def _catalog(session) -> VehicleCatalogService:
    return VehicleCatalogService(
        VehicleBrandRepository(session),
        VehicleModelRepository(session),
    )


def test_applicability_maps_to_vehicle_type() -> None:
    assert PARTS_APPLICABILITY_TO_VEHICLE_TYPE["passenger_cars"] == VehicleType.car
    assert PARTS_APPLICABILITY_TO_VEHICLE_TYPE["cargo"] == VehicleType.truck
    assert PARTS_APPLICABILITY_TO_VEHICLE_TYPE["buses"] == VehicleType.bus
    assert PARTS_APPLICABILITY_TO_VEHICLE_TYPE["special_equipment"] == VehicleType.special
    assert PARTS_APPLICABILITY_TO_VEHICLE_TYPE["farm_machinery"] == VehicleType.agricultural
    assert PARTS_APPLICABILITY_TO_VEHICLE_TYPE["moto"] == VehicleType.motorcycle
    assert PARTS_APPLICABILITY_TO_VEHICLE_TYPE["electric"] == VehicleType.electric
    assert PARTS_APPLICABILITY_TO_VEHICLE_TYPE["bicycles"] == VehicleType.bicycle
    assert PARTS_APPLICABILITY_TO_VEHICLE_TYPE["watercraft"] == VehicleType.watercraft
    assert PARTS_APPLICABILITY_TO_VEHICLE_TYPE["trailers"] == VehicleType.trailer
    assert resolve_catalog_vehicle_type(applicability="passenger_cars") == VehicleType.car
    assert resolve_catalog_vehicle_type(applicability="cargo") == VehicleType.truck
    assert resolve_catalog_vehicle_type(applicability="moto") == VehicleType.motorcycle
    assert resolve_catalog_vehicle_type(applicability="farm_machinery") == (
        VehicleType.agricultural
    )
    assert resolve_catalog_vehicle_type(vehicle_type="truck") == VehicleType.truck
    assert resolve_catalog_vehicle_type() is None

    # Every Step1 option must have a mapper entry.
    assert {v for v, _ in PARTS_VEHICLE_APPLICABILITY_OPTIONS} == set(
        PARTS_APPLICABILITY_TO_VEHICLE_TYPE
    )


def test_passenger_cars_returns_car_brands_not_trucks() -> None:
    async def _run() -> None:
        async with async_session_maker() as session:
            svc = _catalog(session)
            car_type = await svc.list_brands(vehicle_type=VehicleType.car)
            car_app = await svc.list_brands(
                vehicle_type=resolve_catalog_vehicle_type(
                    applicability="passenger_cars"
                )
            )
            car_slugs = {b.slug for b in car_type}
            assert car_slugs == {b.slug for b in car_app}
            assert "toyota" in car_slugs
            assert "kamaz" not in car_slugs
            assert "volvo-trucks" not in car_slugs
            assert all(b.vehicle_type == VehicleType.car for b in car_type)
        await engine.dispose()

    asyncio.run(_run())


def test_cargo_returns_truck_brands_not_passenger() -> None:
    async def _run() -> None:
        async with async_session_maker() as session:
            svc = _catalog(session)
            trucks = await svc.list_brands(vehicle_type=VehicleType.truck)
            cargo = await svc.list_brands(
                vehicle_type=resolve_catalog_vehicle_type(applicability="cargo")
            )
            truck_slugs = {b.slug for b in trucks}
            assert truck_slugs == {b.slug for b in cargo}
            assert "kamaz" in truck_slugs
            assert "toyota" not in truck_slugs
            assert "mercedes-benz" not in truck_slugs
            assert all(b.vehicle_type == VehicleType.truck for b in trucks)
        await engine.dispose()

    asyncio.run(_run())


def test_cargo_models_exclude_passenger_car_models() -> None:
    async def _run() -> None:
        async with async_session_maker() as session:
            svc = _catalog(session)
            kamaz = await svc.list_models_for_brand(
                "kamaz", vehicle_type=VehicleType.truck
            )
            names = {m.name for m in kamaz}
            assert names & {"5490", "6520", "43118"}
            assert "Camry" not in names
            assert "Corolla" not in names

            try:
                await svc.list_models_for_brand(
                    "toyota", vehicle_type=VehicleType.truck
                )
                raised = False
            except EntityNotFoundError:
                raised = True
            assert raised, "toyota must not resolve under truck vehicle_type"

            toyota = await svc.list_models_for_brand(
                "toyota", vehicle_type=VehicleType.car
            )
            car_names = {m.name for m in toyota}
            assert len(car_names) > 0
            assert "5490" not in car_names
        await engine.dispose()

    asyncio.run(_run())


def test_vehicle_type_plus_brand_scopes_models() -> None:
    async def _run() -> None:
        async with async_session_maker() as session:
            svc = _catalog(session)
            trucks = await svc.list_brands(vehicle_type=VehicleType.truck)
            assert trucks
            slug = trucks[0].slug
            models = await svc.list_models_for_brand(
                slug, vehicle_type=VehicleType.truck
            )
            for row in models:
                assert row.brand_slug == slug
        await engine.dispose()

    asyncio.run(_run())


def test_draft_roundtrip_keeps_vehicle_context() -> None:
    draft = encode_parts_draft_path(
        applicability="cargo",
        part_section="brakes",
        part_name="brake_pads",
        brand="KamAZ",
        model="5490",
        year="2018",
        condition="used",
        city="Бишкек",
    )
    restored = decode_parts_draft_path(draft)
    assert restored["vehicle_applicability"] == "cargo"
    assert restored["brand"] == "KamAZ"
    assert restored["model"] == "5490"

    passenger = encode_parts_draft_path(
        applicability="passenger_cars",
        part_section="brakes",
        part_name="brake_pads",
        brand="Toyota",
        model="Camry",
        year="2015",
        condition="used",
        city="Бишкек",
    )
    restored_p = decode_parts_draft_path(passenger)
    assert restored_p["vehicle_applicability"] == "passenger_cars"
    assert restored_p["brand"] == "Toyota"


def test_step1_applicability_regression() -> None:
    """STEP 1 applicability SoT is catalog/constants; picker parent has no live schema."""
    from app.seeds.parts_passenger_cars import build_passenger_cars_catalog

    values = [v for v, _ in PARTS_VEHICLE_APPLICABILITY_OPTIONS]
    assert "passenger_cars" in values
    assert "cargo" in values
    assert len(values) == 10

    cat = build_passenger_cars_catalog()
    assert "vehicle_applicability" in cat["path_fields"]

    async def _run() -> None:
        async with async_session_maker() as session:
            cat_id = int(
                (
                    await session.execute(
                        text(
                            "SELECT id FROM categories "
                            "WHERE slug = 'transport-auto-parts' LIMIT 1"
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
            # P1 hygiene: transport-auto-parts is picker-only (no live core_fields).
            assert parent_fields == 0
        await engine.dispose()

    asyncio.run(_run())


def test_passenger_catalog_sections_unchanged() -> None:
    from app.seeds.parts_passenger_cars import build_passenger_cars_catalog

    cat = build_passenger_cars_catalog()
    assert len(cat["sections"]) == 15
    assert cat["applicability"] == "passenger_cars"


def test_brands_endpoint_accepts_vehicle_type_query() -> None:
    """Live-API smoke: vehicle_type query (avoids Win/asyncpg TestClient dispose flake)."""
    import json
    import urllib.error
    import urllib.request

    url = "http://127.0.0.1:8000/api/v1/vehicles/brands?vehicle_type=truck"
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            status = resp.status
            body = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError) as exc:
        raise AssertionError(f"backend not reachable for brands smoke: {exc}") from exc

    assert status == 200
    assert body
    assert all(b.get("vehicle_type") == "truck" for b in body)
    slugs = {b["slug"] for b in body}
    assert "kamaz" in slugs
    assert "toyota" not in slugs
