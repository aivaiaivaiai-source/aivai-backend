from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.core.exceptions import AppException
from app.models.category_enums import CategoryFieldType
from app.models.enums import Currency, ListingStatus
from app.models.listing_field_value import ListingFieldValue
from app.repositories.listing_field_value_repository import ListingFieldValueRepository
from app.schemas.category import CategoryRead
from app.schemas.listing import ListingCreate, ListingRead
from app.services.listing_field_value_service import ListingFieldValueService
from app.services.listing_service import ListingService


def _category_with_fields(
    *,
    category_id: int = 10,
    core: list[tuple[str, CategoryFieldType]] | None = None,
    optional: list[tuple[str, CategoryFieldType]] | None = None,
) -> SimpleNamespace:
    core_rows = [
        SimpleNamespace(
            field_key=key,
            field_type=ftype,
            is_required=True,
            options=None,
        )
        for key, ftype in (core or [])
    ]
    optional_rows = [
        SimpleNamespace(
            field_key=key,
            field_type=ftype,
            is_required=False,
            options=None,
        )
        for key, ftype in (optional or [])
    ]
    return SimpleNamespace(
        id=category_id,
        core_fields=core_rows,
        optional_fields=optional_rows,
    )


def _service(
    *,
    category: SimpleNamespace | None = None,
    brand: SimpleNamespace | None = None,
    model: SimpleNamespace | None = None,
) -> ListingFieldValueService:
    categories = AsyncMock()
    categories.get_with_intelligence = AsyncMock(
        return_value=category
        or _category_with_fields(
            core=[
                ("city", CategoryFieldType.city),
                ("year", CategoryFieldType.year),
                ("brand", CategoryFieldType.brand),
                ("model", CategoryFieldType.model),
            ]
        )
    )
    field_values = AsyncMock(spec=ListingFieldValueRepository)
    field_values.replace_for_listing = AsyncMock(side_effect=lambda _lid, rows: rows)

    brands = AsyncMock()
    brands.get_by_id = AsyncMock(return_value=brand)
    brands.get_by_slug = AsyncMock(return_value=brand)

    models = AsyncMock()
    models.get_by_id = AsyncMock(return_value=model)
    models.get_by_brand_and_slug = AsyncMock(return_value=model)

    aliases = AsyncMock()
    aliases.find_by_keys = AsyncMock(return_value=None)

    return ListingFieldValueService(categories, field_values, brands, models, aliases)


@pytest.mark.asyncio
async def test_replace_from_known_fields_valid_city_and_year() -> None:
    svc = _service(
        category=_category_with_fields(
            core=[
                ("city", CategoryFieldType.city),
                ("year", CategoryFieldType.year),
            ]
        )
    )
    rows = await svc.replace_from_known_fields(
        listing_id=1,
        category_id=10,
        known_fields={"city": "Bishkek", "year": "2018", "title": "ignored"},
    )
    assert len(rows) == 2
    by_key = {row.field_key: row for row in rows}
    assert by_key["city"].value_text == "Bishkek"
    assert by_key["year"].value_int == 2018


@pytest.mark.asyncio
async def test_invalid_field_key_rejected() -> None:
    svc = _service(category=_category_with_fields(core=[("city", CategoryFieldType.city)]))
    with pytest.raises(AppException) as exc:
        await svc.replace_from_known_fields(
            listing_id=1,
            category_id=10,
            known_fields={"mileage": "120000"},
        )
    assert exc.value.status_code == 400
    assert exc.value.error_code == "INVALID_LISTING_FIELD"


@pytest.mark.asyncio
async def test_wrong_type_rejected() -> None:
    svc = _service(category=_category_with_fields(core=[("year", CategoryFieldType.year)]))
    with pytest.raises(AppException) as exc:
        await svc.replace_from_known_fields(
            listing_id=1,
            category_id=10,
            known_fields={"year": "not-a-number"},
        )
    assert exc.value.error_code == "INVALID_LISTING_FIELD"


@pytest.mark.asyncio
async def test_brand_model_fk_resolution() -> None:
    brand = SimpleNamespace(id=7, is_enabled=True, slug="toyota")
    model = SimpleNamespace(id=42, brand_id=7, is_enabled=True, slug="camry")
    svc = _service(
        category=_category_with_fields(
            core=[
                ("brand", CategoryFieldType.brand),
                ("model", CategoryFieldType.model),
            ]
        ),
        brand=brand,
        model=model,
    )
    rows = await svc.replace_from_known_fields(
        listing_id=1,
        category_id=10,
        known_fields={"brand": "toyota", "model": "camry"},
    )
    by_key = {row.field_key: row for row in rows}
    assert by_key["brand"].ref_brand_id == 7
    assert by_key["model"].ref_model_id == 42


@pytest.mark.asyncio
async def test_listing_service_rolls_back_on_invalid_field_values() -> None:
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()

    listing_repo = AsyncMock()
    category_repo = AsyncMock()
    category_repo.get_by_id = AsyncMock(
        return_value=SimpleNamespace(id=10, slug="transport-cars")
    )

    created_listing = SimpleNamespace(
        id=99,
        title="Test",
        description=None,
        price=Decimal("1000"),
        currency=Currency.KGS,
        status=ListingStatus.draft,
        owner_id=1,
        category_id=10,
        uses_placeholder_image=False,
        images=[],
        category=SimpleNamespace(id=10, slug="transport-cars"),
    )
    listing_repo.create = AsyncMock(return_value=created_listing)
    listing_repo.get_by_id = AsyncMock(return_value=created_listing)

    field_values = AsyncMock()
    field_values.replace_from_known_fields = AsyncMock(
        side_effect=AppException("bad field", status_code=400, code="INVALID_LISTING_FIELD")
    )

    notifications = AsyncMock()
    notifications.emit_saved_search_alerts_for_listing = AsyncMock()

    service = ListingService(
        session,
        listing_repo,
        category_repo,
        notifications,
        field_values,
    )

    with pytest.raises(AppException):
        await service.create_listing(
            ListingCreate(
                title="Test",
                description=None,
                price=Decimal("1000"),
                category_id=10,
                currency=Currency.KGS,
                status=ListingStatus.draft,
            ),
            owner_id=1,
            known_fields={"unknown_field": "x"},
        )

    session.rollback.assert_awaited_once()
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_existing_create_listing_without_known_fields_still_works() -> None:
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()

    listing_repo = AsyncMock()
    category_repo = AsyncMock()
    category_repo.get_by_id = AsyncMock(
        return_value=SimpleNamespace(id=10, slug="transport-cars")
    )

    created_listing = SimpleNamespace(
        id=99,
        title="Test",
        description=None,
        price=Decimal("1000"),
        currency=Currency.KGS,
        status=ListingStatus.draft,
        owner_id=1,
        category_id=10,
        uses_placeholder_image=False,
        images=[],
        category=SimpleNamespace(id=10, slug="transport-cars"),
    )
    listing_repo.create = AsyncMock(return_value=created_listing)
    listing_repo.get_by_id = AsyncMock(return_value=created_listing)

    field_values = AsyncMock()
    notifications = AsyncMock()

    service = ListingService(session, listing_repo, category_repo, notifications, field_values)
    now = datetime.now(UTC)
    expected = ListingRead(
        id=99,
        title="Test",
        description=None,
        price=Decimal("1000"),
        currency=Currency.KGS,
        status=ListingStatus.draft,
        owner_id=1,
        category_id=10,
        category=CategoryRead(id=10, name="Cars", slug="transport-cars", parent_id=None),
        images=[],
        created_at=now,
        updated_at=now,
    )
    with patch.object(ListingRead, "model_validate", return_value=expected):
        result = await service.create_listing(
            ListingCreate(
                title="Test",
                description=None,
                price=Decimal("1000"),
                category_id=10,
                currency=Currency.KGS,
                status=ListingStatus.draft,
            ),
            owner_id=1,
        )

    assert result.id == 99
    field_values.replace_from_known_fields.assert_not_awaited()
    session.commit.assert_awaited_once()


def test_single_value_check_enforced_in_service() -> None:
    row = ListingFieldValue(field_key="city", value_text="Bishkek", value_int=1)
    with pytest.raises(AppException):
        ListingFieldValueService._ensure_single_value(row)


@pytest.mark.integration
def test_unique_and_cascade_constraints_in_database() -> None:
    import subprocess

    docker_check = subprocess.run(
        ["docker", "exec", "aivai_backend-db-1", "psql", "-U", "aivai", "-d", "aivai", "-tAc", "SELECT 1"],
        capture_output=True,
        text=True,
        check=False,
    )
    if docker_check.returncode != 0:
        pytest.skip("Docker PostgreSQL is unavailable")

    table_exists = subprocess.run(
        [
            "docker",
            "exec",
            "aivai_backend-db-1",
            "psql",
            "-U",
            "aivai",
            "-d",
            "aivai",
            "-tAc",
            "SELECT to_regclass('public.listing_field_values')",
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    if table_exists != "listing_field_values":
        pytest.skip("listing_field_values table is not migrated")

    user_id = subprocess.run(
        [
            "docker",
            "exec",
            "aivai_backend-db-1",
            "psql",
            "-U",
            "aivai",
            "-d",
            "aivai",
            "-tAc",
            "SELECT id FROM users ORDER BY id DESC LIMIT 1",
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip().splitlines()[0]
    category_id = subprocess.run(
        [
            "docker",
            "exec",
            "aivai_backend-db-1",
            "psql",
            "-U",
            "aivai",
            "-d",
            "aivai",
            "-tAc",
            "SELECT id FROM categories LIMIT 1",
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    listing_id = subprocess.run(
        [
            "docker",
            "exec",
            "aivai_backend-db-1",
            "psql",
            "-U",
            "aivai",
            "-d",
            "aivai",
            "-tAc",
            (
                "INSERT INTO listings (title, price, currency, status, owner_id, category_id) "
                f"VALUES ('Field Value Test', 1000, 'KGS', 'draft', {user_id}, {category_id}) RETURNING id"
            ),
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip().splitlines()[0]

    subprocess.run(
        [
            "docker",
            "exec",
            "aivai_backend-db-1",
            "psql",
            "-U",
            "aivai",
            "-d",
            "aivai",
            "-c",
            (
                "INSERT INTO listing_field_values (listing_id, field_key, value_text) "
                f"VALUES ({listing_id}, 'city', 'Bishkek')"
            ),
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    duplicate = subprocess.run(
        [
            "docker",
            "exec",
            "aivai_backend-db-1",
            "psql",
            "-U",
            "aivai",
            "-d",
            "aivai",
            "-tAc",
            (
                "INSERT INTO listing_field_values (listing_id, field_key, value_text) "
                f"VALUES ({listing_id}, 'city', 'Osh')"
            ),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert duplicate.returncode != 0

    subprocess.run(
        [
            "docker",
            "exec",
            "aivai_backend-db-1",
            "psql",
            "-U",
            "aivai",
            "-d",
            "aivai",
            "-c",
            f"DELETE FROM listings WHERE id = {listing_id}",
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    remaining = subprocess.run(
        [
            "docker",
            "exec",
            "aivai_backend-db-1",
            "psql",
            "-U",
            "aivai",
            "-d",
            "aivai",
            "-tAc",
            f"SELECT count(*) FROM listing_field_values WHERE listing_id = {listing_id}",
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    assert remaining == "0"
