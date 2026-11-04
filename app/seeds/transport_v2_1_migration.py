# -*- coding: utf-8 -*-
"""Transport V2.1 catalog migration — idempotent raw SQL via AsyncSession."""
from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.seeds.transport_v2_1 import (
    ALIAS_RETARGET,
    AUTO_SERVICES_CHILD_SLUGS,
    BODY_CHILD_SLUGS,
    BUSES_L2_CHILD_SLUGS,
    L1_ACTIVE,
    MERGE_LISTING_REMAP,
    MIGRATION_MARKER,
    MOVE_PARENT,
    NEW_CATEGORIES,
    RENAME_NAMES,
    RETIRE_BRANCH_ROOT_SLUGS,
    RETIRE_LEAF_SLUGS,
    SERVICES_PENDING,
    SNAPSHOT_DIR,
    parts_vehicle_applicability_options_json,
)

logger = logging.getLogger(__name__)


@dataclass
class PreflightResult:
    ok: bool = True
    listing_counts: dict[str, int] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    already_applied: bool = False


@dataclass
class MigrationResult:
    snapshot_path: str
    snapshot_sha256: str
    created: list[str] = field(default_factory=list)
    renamed: list[str] = field(default_factory=list)
    moved: list[str] = field(default_factory=list)
    retired: list[str] = field(default_factory=list)
    listings_remapped: int = 0
    aliases_retargeted: int = 0
    services_pending: dict[str, str] = field(default_factory=dict)
    dry_run: bool = False


async def _slug_map(session: AsyncSession) -> dict[str, dict[str, Any]]:
    rows = (
        await session.execute(
            text(
                "SELECT id, slug, name, parent_id, is_active, sort_order, entity_type "
                "FROM categories"
            )
        )
    ).mappings().all()
    return {r["slug"]: dict(r) for r in rows}


async def preflight(session: AsyncSession) -> PreflightResult:
    result = PreflightResult()
    marker = (
        await session.execute(
            text(
                "SELECT 1 FROM category_aliases WHERE alias = :a AND locale = 'ru' LIMIT 1"
            ),
            {"a": MIGRATION_MARKER},
        )
    ).scalar_one_or_none()
    if marker:
        result.already_applied = True

    slugs = await _slug_map(session)
    if "transport" not in slugs:
        result.ok = False
        result.errors.append("transport root missing")
        return result
    if "transport-car-sale" not in slugs:
        result.ok = False
        result.errors.append("transport-car-sale missing — abort")
        return result

    watch = set(MERGE_LISTING_REMAP) | set(RETIRE_LEAF_SLUGS) | set(RETIRE_BRANCH_ROOT_SLUGS)
    for slug in sorted(watch):
        row = slugs.get(slug)
        if not row:
            continue
        cnt = int(
            (
                await session.execute(
                    text("SELECT COUNT(*) FROM listings WHERE category_id = :id"),
                    {"id": row["id"]},
                )
            ).scalar_one()
        )
        result.listing_counts[slug] = cnt
    return result


async def create_snapshot(session: AsyncSession) -> tuple[Path, str]:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    path = SNAPSHOT_DIR / f"pre_v2_1_{ts}.json"
    tree = (
        await session.execute(
            text(
                """
                WITH RECURSIVE tr AS (
                  SELECT id FROM categories WHERE slug = 'transport'
                  UNION ALL
                  SELECT c.id FROM categories c JOIN tr ON c.parent_id = tr.id
                )
                SELECT c.id, c.slug, c.name, c.parent_id, c.is_active, c.sort_order
                FROM categories c JOIN tr ON c.id = tr.id
                ORDER BY c.id
                """
            )
        )
    ).mappings().all()
    listings = (
        await session.execute(
            text(
                """
                WITH RECURSIVE tr AS (
                  SELECT id FROM categories WHERE slug = 'transport'
                  UNION ALL
                  SELECT c.id FROM categories c JOIN tr ON c.parent_id = tr.id
                )
                SELECT category_id, status::text AS status, COUNT(*) AS cnt
                FROM listings WHERE category_id IN (SELECT id FROM tr)
                GROUP BY category_id, status
                """
            )
        )
    ).mappings().all()
    payload = {
        "created_at": ts,
        "categories": [dict(r) for r in tree],
        "listing_counts": [dict(r) for r in listings],
    }
    raw = json.dumps(payload, ensure_ascii=False, indent=2, default=str).encode("utf-8")
    path.write_bytes(raw)
    return path, hashlib.sha256(raw).hexdigest()


async def _ensure_category(
    session: AsyncSession,
    *,
    parent_slug: str,
    slug: str,
    name: str,
    sort_order: int,
    slugs: dict[str, dict[str, Any]],
) -> bool:
    if slug in slugs:
        return False
    parent = slugs.get(parent_slug)
    if parent is None:
        raise RuntimeError(f"Missing parent {parent_slug} for {slug}")
    await session.execute(
        text(
            """
            INSERT INTO categories
              (name, slug, parent_id, entity_type, sort_order, is_active, requires_city, created_at, updated_at)
            VALUES
              (:name, :slug, :parent_id, 'object', :sort_order, true, true, NOW(), NOW())
            """
        ),
        {
            "name": name,
            "slug": slug,
            "parent_id": parent["id"],
            "sort_order": sort_order,
        },
    )
    return True


async def _deactivate_subtree(
    session: AsyncSession,
    root_id: int,
    *,
    exclude_ids: set[int],
) -> list[int]:
    rows = (
        await session.execute(
            text(
                """
                WITH RECURSIVE tr AS (
                  SELECT id FROM categories WHERE id = :root
                  UNION ALL
                  SELECT c.id FROM categories c JOIN tr ON c.parent_id = tr.id
                )
                SELECT id FROM tr
                """
            ),
            {"root": root_id},
        )
    ).scalars().all()
    deactivated: list[int] = []
    for cid in rows:
        if cid in exclude_ids:
            continue
        await session.execute(
            text(
                "UPDATE categories SET is_active = false, updated_at = NOW() WHERE id = :id AND is_active = true"
            ),
            {"id": cid},
        )
        deactivated.append(int(cid))
    return deactivated


async def run_migration(
    session: AsyncSession,
    *,
    dry_run: bool = False,
) -> MigrationResult:
    pf = await preflight(session)
    if not pf.ok:
        raise RuntimeError(f"Preflight failed: {pf.errors}")

    snap_path, snap_hash = await create_snapshot(session)
    result = MigrationResult(
        snapshot_path=str(snap_path),
        snapshot_sha256=snap_hash,
        services_pending=dict(SERVICES_PENDING),
        dry_run=dry_run,
    )
    if dry_run:
        return result

    if pf.already_applied:
        logger.info("Transport V2.1 marker present — running idempotent sync")

    slugs = await _slug_map(session)

    # 1) Create new nodes (parents first via multipass)
    pending = list(NEW_CATEGORIES)
    for _ in range(6):
        if not pending:
            break
        next_pending: list[tuple[str, str, str, int]] = []
        for parent_slug, slug, name, sort_order in pending:
            if slug in slugs:
                continue
            if parent_slug not in slugs:
                next_pending.append((parent_slug, slug, name, sort_order))
                continue
            created = await _ensure_category(
                session,
                parent_slug=parent_slug,
                slug=slug,
                name=name,
                sort_order=sort_order,
                slugs=slugs,
            )
            if created:
                result.created.append(slug)
                await session.flush()
                slugs = await _slug_map(session)
        pending = next_pending
    if pending:
        raise RuntimeError(f"Could not create categories: {pending}")

    slugs = await _slug_map(session)

    # 2) Move body children under Кузовные детали (renamed to Кузов…)
    body_parent = slugs.get("transport-auto-parts-kuzovnye-detali")
    if body_parent:
        for child_slug in BODY_CHILD_SLUGS:
            child = slugs.get(child_slug)
            if not child:
                continue
            if child["parent_id"] == body_parent["id"]:
                continue
            await session.execute(
                text(
                    "UPDATE categories SET parent_id = :pid, updated_at = NOW() WHERE id = :id"
                ),
                {"pid": body_parent["id"], "id": child["id"]},
            )
            result.moved.append(child_slug)

    # 3) Move parents (buses) + canonical child sort under buses L2
    bus_child_sort = {
        "transport-commercial-avtobusy": 10,
        "transport-commercial-mikroavtobusy": 20,
        "transport-buses-avtodoma": 30,
    }
    for slug, new_parent_slug in MOVE_PARENT.items():
        row = slugs.get(slug)
        parent = slugs.get(new_parent_slug)
        if not row or not parent:
            continue
        await session.execute(
            text(
                "UPDATE categories SET parent_id = :pid, is_active = true, "
                "sort_order = :ord, updated_at = NOW() WHERE id = :id"
            ),
            {
                "pid": parent["id"],
                "ord": bus_child_sort.get(slug, row["sort_order"]),
                "id": row["id"],
            },
        )
        if row["parent_id"] != parent["id"]:
            result.moved.append(slug)

    avtodoma = slugs.get("transport-buses-avtodoma")
    buses_l2 = slugs.get("transport-buses-microbuses-motorhomes")
    if avtodoma and buses_l2:
        await session.execute(
            text(
                "UPDATE categories SET parent_id = :pid, is_active = true, "
                "sort_order = 30, updated_at = NOW() WHERE id = :id"
            ),
            {"pid": buses_l2["id"], "id": avtodoma["id"]},
        )

    await session.flush()
    slugs = await _slug_map(session)

    # 4) Remap listings for merges
    remapped = 0
    for src_slug, dst_slug in MERGE_LISTING_REMAP.items():
        src = slugs.get(src_slug)
        dst = slugs.get(dst_slug)
        if not src or not dst:
            continue
        res = await session.execute(
            text(
                "UPDATE listings SET category_id = :dst, updated_at = NOW() "
                "WHERE category_id = :src RETURNING id"
            ),
            {"dst": dst["id"], "src": src["id"]},
        )
        remapped += len(res.fetchall())
    result.listings_remapped = remapped

    # 5) Renames
    for slug, name in RENAME_NAMES.items():
        row = slugs.get(slug)
        if not row:
            continue
        if row["name"] == name:
            continue
        await session.execute(
            text("UPDATE categories SET name = :name, updated_at = NOW() WHERE id = :id"),
            {"name": name, "id": row["id"]},
        )
        result.renamed.append(slug)

    # 6) L1 order + activate desired L1; deactivate non-desired active L1 under transport
    transport = slugs["transport"]
    desired_l1 = {slug for slug, _, _ in L1_ACTIVE}
    for slug, name, sort_order in L1_ACTIVE:
        row = slugs.get(slug)
        if not row:
            raise RuntimeError(f"Required L1 missing: {slug}")
        await session.execute(
            text(
                "UPDATE categories SET name = :name, sort_order = :ord, parent_id = :pid, "
                "is_active = true, updated_at = NOW() WHERE id = :id"
            ),
            {
                "name": name,
                "ord": sort_order,
                "pid": transport["id"],
                "id": row["id"],
            },
        )

    # Soft-deactivate other active L2 under transport (legacy / non-canonical)
    other_active = (
        await session.execute(
            text(
                "SELECT id, slug FROM categories "
                "WHERE parent_id = :pid AND is_active = true"
            ),
            {"pid": transport["id"]},
        )
    ).mappings().all()
    for row in other_active:
        if row["slug"] in desired_l1:
            continue
        await session.execute(
            text(
                "UPDATE categories SET is_active = false, updated_at = NOW() WHERE id = :id"
            ),
            {"id": row["id"]},
        )
        result.retired.append(row["slug"])

    # 7) Retire branch roots (except children already reparented away)
    preserve_ids: set[int] = set()
    for slug in ("transport-commercial-avtobusy", "transport-commercial-mikroavtobusy"):
        if slug in slugs:
            preserve_ids.add(int(slugs[slug]["id"]))
    # never touch car-sale
    preserve_ids.add(int(slugs["transport-car-sale"]["id"]))

    for root_slug in RETIRE_BRANCH_ROOT_SLUGS:
        root = slugs.get(root_slug)
        if not root:
            continue
        deactivated = await _deactivate_subtree(
            session, int(root["id"]), exclude_ids=preserve_ids
        )
        result.retired.extend(str(i) for i in deactivated)

    # 8) Retire explicit leaves
    for slug in RETIRE_LEAF_SLUGS:
        row = slugs.get(slug)
        if not row:
            continue
        if int(row["id"]) in preserve_ids:
            continue
        await session.execute(
            text(
                "UPDATE categories SET is_active = false, updated_at = NOW() WHERE id = :id"
            ),
            {"id": row["id"]},
        )
        result.retired.append(slug)

    # Deactivate commercial/buyback roots themselves if still active
    for root_slug in RETIRE_BRANCH_ROOT_SLUGS:
        row = slugs.get(root_slug)
        if not row:
            continue
        await session.execute(
            text(
                "UPDATE categories SET is_active = false, updated_at = NOW() WHERE id = :id"
            ),
            {"id": row["id"]},
        )
        result.retired.append(root_slug)

    # Ensure auto-services L2 + 10 canonical children stay active
    services = slugs.get("transport-auto-services")
    if services:
        await session.execute(
            text(
                "UPDATE categories SET is_active = true, updated_at = NOW() WHERE id = :id"
            ),
            {"id": services["id"]},
        )
        for child_slug in AUTO_SERVICES_CHILD_SLUGS:
            row = slugs.get(child_slug)
            if not row:
                continue
            await session.execute(
                text(
                    "UPDATE categories SET is_active = true, parent_id = :pid, "
                    "updated_at = NOW() WHERE id = :id"
                ),
                {"pid": services["id"], "id": row["id"]},
            )

    # 9) Alias retarget for light
    alias_n = 0
    for alias, target_slug in ALIAS_RETARGET.items():
        target = slugs.get(target_slug)
        if not target:
            continue
        res = await session.execute(
            text(
                """
                UPDATE category_aliases
                SET category_id = :cid, updated_at = NOW()
                WHERE alias_normalized = :alias OR alias = :alias_raw
                RETURNING id
                """
            ),
            {
                "cid": target["id"],
                "alias": alias.lower(),
                "alias_raw": alias,
            },
        )
        alias_n += len(res.fetchall())
    result.aliases_retargeted = alias_n

    # Remove "фара" from auto-parts root aliases if still pointing wrong — handled by UPDATE above.

    # 10) Marker alias on transport root (idempotent)
    transport_id = slugs["transport"]["id"]
    existing_marker = (
        await session.execute(
            text(
                "SELECT id FROM category_aliases WHERE alias = :a AND category_id = :cid LIMIT 1"
            ),
            {"a": MIGRATION_MARKER, "cid": transport_id},
        )
    ).scalar_one_or_none()
    if existing_marker is None:
        await session.execute(
            text(
                """
                INSERT INTO category_aliases
                  (category_id, alias, alias_normalized, alias_compact, weight, is_enabled, locale, created_at, updated_at)
                VALUES
                  (:cid, :a, :a, :a, 1, false, 'ru', NOW(), NOW())
                """
            ),
            {"cid": transport_id, "a": MIGRATION_MARKER},
        )

    # 11) Core fields for key new/updated branches (minimal working set)
    await _upsert_transport_v21_fields(session, await _slug_map(session))

    await session.commit()
    return result


async def _upsert_transport_v21_fields(
    session: AsyncSession, slugs: dict[str, dict[str, Any]]
) -> None:
    """Ensure publication/search fields exist for non-car-sale Transport V2.1 branches."""
    common = [
        ("city", "Город", "city", 10),
        ("price", "Цена", "price", 20),
        ("condition", "Состояние", "enum", 30),
    ]
    vehicle = [
        ("city", "Город", "city", 10),
        ("brand", "Марка", "brand", 20),
        ("model", "Модель", "model", 30),
        ("year", "Год", "year", 40),
        ("powertrain", "Силовая установка", "enum", 50),
        ("price", "Цена", "price", 60),
        ("condition", "Состояние", "enum", 70),
    ]
    parts = [
        ("city", "Город", "city", 10),
        ("vehicle_applicability", "Для какого транспорта", "enum", 20),
        ("part_section", "Раздел", "string", 30),
        ("part_name", "Название детали", "string", 40),
        ("oem_number", "OEM / артикул", "string", 50),
        ("brand", "Марка совместимости", "brand", 60),
        ("model", "Модель совместимости", "model", 70),
        ("condition", "Состояние", "enum", 80),
        ("completeness", "Комплектность", "enum", 90),
        ("price", "Цена", "price", 100),
    ]
    tires = [
        ("city", "Город", "city", 10),
        ("vehicle_applicability", "Для какого транспорта", "enum", 20),
        ("tire_size", "Размер", "string", 30),
        ("season", "Сезонность", "enum", 40),
        ("brand", "Бренд", "brand", 50),
        ("condition", "Состояние", "enum", 60),
        ("price", "Цена", "price", 70),
    ]
    rental = [
        ("city", "Город", "city", 10),
        ("rental_offer_type", "Тип объявления", "enum", 20),
        ("vehicle_type", "Вид транспорта", "enum", 30),
        ("price", "Ставка", "price", 40),
        ("rental_period_unit", "Период", "enum", 50),
        ("min_term", "Минимальный срок", "string", 60),
        ("deposit", "Залог", "price", 70),
    ]
    buses = [
        ("city", "Город", "city", 10),
        ("brand", "Марка", "brand", 20),
        ("model", "Модель", "model", 30),
        ("year", "Год", "year", 40),
        ("seats", "Число мест", "number", 50),
        ("passenger_cargo", "Грузопассажирское исполнение", "enum", 60),
        ("price", "Цена", "price", 70),
        ("condition", "Состояние", "enum", 80),
    ]
    trailers = [
        ("city", "Город", "city", 10),
        ("construction", "Конструкция", "enum", 20),
        ("body_type", "Кузов", "enum", 30),
        ("purpose", "Назначение", "enum", 40),
        ("tow_vehicle", "Тягач", "enum", 50),
        ("payload_kg", "Грузоподъёмность", "number", 60),
        ("price", "Цена", "price", 70),
        ("condition", "Состояние", "enum", 80),
    ]

    targets: dict[str, list[tuple[str, str, str, int]]] = {
        "transport-auto-parts": parts,
        "transport-tires-wheels": tires,
        "transport-accessories-tuning": common
        + [("item_type", "Вид", "string", 15)],
        "transport-moto-tech": vehicle,
        "transport-electric": [
            ("city", "Город", "city", 10),
            ("brand", "Бренд", "brand", 20),
            ("model", "Модель", "model", 30),
            ("battery_capacity", "Ёмкость батареи", "string", 40),
            ("power_kw", "Мощность", "number", 50),
            ("price", "Цена", "price", 60),
            ("condition", "Состояние", "enum", 70),
        ],
        "transport-bicycles": [
            ("city", "Город", "city", 10),
            ("brand", "Бренд", "brand", 20),
            ("frame_size", "Размер рамы", "string", 30),
            ("wheel_diameter", "Диаметр колёс", "string", 40),
            ("electric_assist", "Электропривод", "enum", 50),
            ("foldable", "Складной", "enum", 60),
            ("age_group", "Возрастная группа", "enum", 70),
            ("price", "Цена", "price", 80),
            ("condition", "Состояние", "enum", 90),
        ],
        "transport-cargo": vehicle
        + [("payload_kg", "Грузоподъёмность", "number", 55)],
        "transport-buses-microbuses-motorhomes": buses,
        "transport-special-equipment": vehicle
        + [("hours", "Моточасы", "number", 55)],
        "transport-farm-machinery": vehicle
        + [("hours", "Моточасы", "number", 55)],
        "transport-watercraft": common
        + [
            ("item_type", "Тип", "string", 15),
            ("hull_material", "Материал корпуса", "string", 25),
            ("length_m", "Длина", "number", 35),
            ("engine_included", "Мотор в комплекте", "enum", 45),
        ],
        "transport-trailers": trailers,
        "transport-rental": rental,
    }

    for slug, fields in targets.items():
        row = slugs.get(slug)
        if not row:
            continue
        cat_id = int(row["id"])
        for key, label, ftype, sort_order in fields:
            exists = (
                await session.execute(
                    text(
                        "SELECT id FROM category_core_fields "
                        "WHERE category_id = :cid AND field_key = :key"
                    ),
                    {"cid": cat_id, "key": key},
                )
            ).scalar_one_or_none()
            if exists:
                await session.execute(
                    text(
                        "UPDATE category_core_fields SET label = :label, field_type = CAST(:ftype AS category_field_type_enum), "
                        "sort_order = :ord, updated_at = NOW() WHERE id = :id"
                    ),
                    {
                        "label": label,
                        "ftype": ftype,
                        "ord": sort_order,
                        "id": exists,
                    },
                )
            else:
                await session.execute(
                    text(
                        """
                        INSERT INTO category_core_fields
                          (category_id, field_key, label, field_type, is_required, sort_order, created_at, updated_at)
                        VALUES
                          (:cid, :key, :label, CAST(:ftype AS category_field_type_enum), false, :ord, NOW(), NOW())
                        """
                    ),
                    {
                        "cid": cat_id,
                        "key": key,
                        "label": label,
                        "ftype": ftype,
                        "ord": sort_order,
                    },
                )

        # Matching search filters (subset)
        filter_keys = [(f[0], f[1], f[2], f[3]) for f in fields[:6]]
        for key, label, ftype, sort_order in filter_keys:
            exists = (
                await session.execute(
                    text(
                        "SELECT id FROM category_filters "
                        "WHERE category_id = :cid AND filter_key = :key"
                    ),
                    {"cid": cat_id, "key": key},
                )
            ).scalar_one_or_none()
            if exists:
                continue
            await session.execute(
                text(
                    """
                    INSERT INTO category_filters
                      (category_id, filter_key, label, filter_type, sort_order, config, created_at, updated_at)
                    VALUES
                      (:cid, :key, :label, CAST(:ftype AS category_filter_type_enum), :ord, '{}'::jsonb, NOW(), NOW())
                    """
                ),
                {
                    "cid": cat_id,
                    "key": key,
                    "label": label,
                    "ftype": "select" if ftype == "enum" else "text",
                    "ord": sort_order,
                },
            )

    await _ensure_parts_vehicle_applicability_options(session, slugs)


async def _ensure_parts_vehicle_applicability_options(
    session: AsyncSession, slugs: dict[str, dict[str, Any]]
) -> None:
    """Parts Step 1: populate vehicle_applicability enum options (idempotent)."""
    row = slugs.get("transport-auto-parts")
    if not row:
        return
    cat_id = int(row["id"])
    options = parts_vehicle_applicability_options_json()
    payload = json.dumps(options, ensure_ascii=False)
    await session.execute(
        text(
            """
            UPDATE category_core_fields
            SET options = CAST(:opts AS jsonb),
                label = 'Для какого транспорта',
                field_type = CAST('enum' AS category_field_type_enum),
                updated_at = NOW()
            WHERE category_id = :cid AND field_key = 'vehicle_applicability'
            """
        ),
        {"cid": cat_id, "opts": payload},
    )
    await session.execute(
        text(
            """
            UPDATE category_filters
            SET config = CAST(:opts AS jsonb),
                label = 'Для какого транспорта',
                updated_at = NOW()
            WHERE category_id = :cid AND filter_key = 'vehicle_applicability'
            """
        ),
        {"cid": cat_id, "opts": payload},
    )


async def verify_post_migration(session: AsyncSession) -> dict[str, Any]:
    slugs = await _slug_map(session)
    transport_id = slugs["transport"]["id"]
    active_l1 = (
        await session.execute(
            text(
                "SELECT slug, name, sort_order FROM categories "
                "WHERE parent_id = :pid AND is_active = true ORDER BY sort_order, id"
            ),
            {"pid": transport_id},
        )
    ).mappings().all()
    active_slugs = [r["slug"] for r in active_l1]
    expected = [s for s, _, _ in L1_ACTIVE]
    forbidden = [
        s
        for s in (
            "transport-commercial",
            "transport-buyback-exchange",
        )
        if slugs.get(s, {}).get("is_active")
    ]
    car = slugs.get("transport-car-sale", {})
    return {
        "active_l1": [dict(r) for r in active_l1],
        "active_l1_slugs": active_slugs,
        "expected_l1": expected,
        "l1_match": active_slugs == expected,
        "forbidden_still_active": forbidden,
        "car_sale_active": bool(car.get("is_active")),
        "car_sale_name": car.get("name"),
        "parts_name": slugs.get("transport-auto-parts", {}).get("name"),
        "buses_parent_active": bool(
            slugs.get("transport-buses-microbuses-motorhomes", {}).get("is_active")
        ),
        "optics_parent": slugs.get("transport-auto-parts-optika-fary-i-fonari", {}).get(
            "parent_id"
        ),
        "kuzov_id": slugs.get("transport-auto-parts-kuzovnye-detali", {}).get("id"),
    }
