"""Transport catalog canonicalization Phase 1 — migration logic (raw SQL)."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.seeds.transport_canonical import (
    AI_SEARCH_TASK_LEGACY_ID_REMAP,
    CANONICAL_MAP_V1_PATH,
    LEGACY_TRANSPORT_IDS,
    PARTS_ALIAS_TO_CANONICAL_SLUG,
    RETIRED_TRANSPORT_SLUGS,
    TRUCKS_ALIAS_TO_CANONICAL_SLUG,
)

SNAPSHOT_DIR = Path(__file__).resolve().parents[2] / ".local" / "transport_canonical_rollback"


@dataclass
class PreflightResult:
    ok: bool
    legacy_listing_counts: dict[int, int] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)


@dataclass
class MigrationResult:
    snapshot_path: str
    snapshot_sha256: str
    filters_migrated: int
    aliases_migrated: int
    core_migrated: int
    routing_rules_updated: int
    ai_tasks_updated: int
    legacy_deactivated: list[int]


async def preflight(session: AsyncSession) -> PreflightResult:
    result = PreflightResult(ok=True)
    for legacy_id in LEGACY_TRANSPORT_IDS:
        count = (
            await session.execute(
                text("SELECT COUNT(*) FROM listings WHERE category_id = :id"),
                {"id": legacy_id},
            )
        ).scalar_one()
        result.legacy_listing_counts[legacy_id] = int(count)
        if count > 0:
            result.ok = False
            result.errors.append(f"legacy category_id={legacy_id} has {count} listing(s)")
    return result


async def _fetch_category_snapshot(session: AsyncSession, cat_id: int) -> dict[str, Any]:
    cat = (
        await session.execute(
            text(
                "SELECT id, slug, name, parent_id, is_active, entity_type, sort_order "
                "FROM categories WHERE id = :id"
            ),
            {"id": cat_id},
        )
    ).mappings().one()
    core = (
        await session.execute(
            text(
                "SELECT field_key, label, field_type, sort_order, ai_hint "
                "FROM category_core_fields WHERE category_id = :id ORDER BY sort_order"
            ),
            {"id": cat_id},
        )
    ).mappings().all()
    opt = (
        await session.execute(
            text(
                "SELECT field_key, label, field_type, sort_order "
                "FROM category_optional_fields WHERE category_id = :id ORDER BY sort_order"
            ),
            {"id": cat_id},
        )
    ).mappings().all()
    filt = (
        await session.execute(
            text(
                "SELECT filter_key, label, filter_type, sort_order, config "
                "FROM category_filters WHERE category_id = :id ORDER BY sort_order"
            ),
            {"id": cat_id},
        )
    ).mappings().all()
    aliases = (
        await session.execute(
            text(
                "SELECT alias, alias_normalized, alias_compact, weight, is_enabled, locale "
                "FROM category_aliases WHERE category_id = :id"
            ),
            {"id": cat_id},
        )
    ).mappings().all()
    return {
        "category": dict(cat),
        "core_fields": [dict(r) for r in core],
        "optional_fields": [dict(r) for r in opt],
        "filters": [dict(r) for r in filt],
        "aliases": [dict(r) for r in aliases],
    }


async def create_rollback_snapshot(session: AsyncSession) -> tuple[Path, str]:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    path = SNAPSHOT_DIR / f"pre_phase1_{ts}.json"

    canonical_ids = (681, 682, 683, 684, 686, 690, 691, 692)
    ids = set(LEGACY_TRANSPORT_IDS) | set(canonical_ids)
    snapshot: dict[str, Any] = {
        "created_at": ts,
        "legacy_ids": list(LEGACY_TRANSPORT_IDS),
        "categories": {},
        "routing_rules": [],
        "ai_search_tasks": [],
        "reference_counts": {},
    }

    for cid in sorted(ids):
        row = (
            await session.execute(
                text("SELECT 1 FROM categories WHERE id = :id"), {"id": cid}
            )
        ).first()
        if row:
            snapshot["categories"][str(cid)] = await _fetch_category_snapshot(session, cid)

    rules = (
        await session.execute(
            text(
                "SELECT id, name, pattern, config, is_active FROM category_ai_rules "
                "WHERE name = 'kamaz_sale' OR config::text LIKE '%transport-truck%'"
            )
        )
    ).mappings().all()
    snapshot["routing_rules"] = [dict(r) for r in rules]

    tasks = (
        await session.execute(
            text("SELECT id, category_ids FROM ai_search_tasks WHERE category_ids::text != '[]'")
        )
    ).mappings().all()
    snapshot["ai_search_tasks"] = [dict(r) for r in tasks]

    for legacy_id in LEGACY_TRANSPORT_IDS:
        snapshot["reference_counts"][str(legacy_id)] = {
            "listings": (
                await session.execute(
                    text("SELECT COUNT(*) FROM listings WHERE category_id = :id"),
                    {"id": legacy_id},
                )
            ).scalar_one(),
        }

    raw = json.dumps(snapshot, ensure_ascii=False, default=str, indent=2)
    path.write_text(raw, encoding="utf-8")
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    path.with_suffix(".sha256").write_text(digest + "\n", encoding="utf-8")
    return path, digest


async def _slug_id_map(session: AsyncSession) -> dict[str, int]:
    rows = (await session.execute(text("SELECT slug, id FROM categories"))).all()
    return {slug: cid for slug, cid in rows}


async def _copy_filters_sql(session: AsyncSession, *, source_id: int, target_id: int) -> int:
    rows = (
        await session.execute(
            text(
                "SELECT filter_key, label, filter_type, sort_order, config "
                "FROM category_filters WHERE category_id = :sid"
            ),
            {"sid": source_id},
        )
    ).mappings().all()
    moved = 0
    for r in rows:
        exists = (
            await session.execute(
                text(
                    "SELECT 1 FROM category_filters "
                    "WHERE category_id = :tid AND filter_key = :key LIMIT 1"
                ),
                {"tid": target_id, "key": r["filter_key"]},
            )
        ).first()
        if exists:
            continue
        await session.execute(
            text(
                "INSERT INTO category_filters "
                "(category_id, filter_key, label, filter_type, sort_order, config, created_at, updated_at) "
                "SELECT :tid, filter_key, label, filter_type, sort_order, config, NOW(), NOW() "
                "FROM category_filters WHERE category_id = :sid AND filter_key = :key"
            ),
            {"tid": target_id, "sid": source_id, "key": r["filter_key"]},
        )
        moved += 1
    return moved


async def _copy_core_sql(session: AsyncSession, *, source_id: int, target_id: int) -> int:
    rows = (
        await session.execute(
            text(
                "SELECT field_key, label, field_type, sort_order, ai_hint, is_required "
                "FROM category_core_fields WHERE category_id = :sid"
            ),
            {"sid": source_id},
        )
    ).mappings().all()
    moved = 0
    for r in rows:
        exists = (
            await session.execute(
                text(
                    "SELECT 1 FROM category_core_fields "
                    "WHERE category_id = :tid AND field_key = :key LIMIT 1"
                ),
                {"tid": target_id, "key": r["field_key"]},
            )
        ).first()
        if exists:
            continue
        await session.execute(
            text(
                "INSERT INTO category_core_fields "
                "(category_id, field_key, label, field_type, is_required, sort_order, ai_hint, created_at, updated_at) "
                "VALUES (:tid, :key, :label, :ftype, :req, :ord, :hint, NOW(), NOW())"
            ),
            {
                "tid": target_id,
                "key": r["field_key"],
                "label": r["label"],
                "ftype": r["field_type"],
                "req": r["is_required"],
                "ord": r["sort_order"],
                "hint": r["ai_hint"],
            },
        )
        moved += 1
    return moved


async def _move_alias(
    session: AsyncSession,
    *,
    alias_text: str,
    source_id: int,
    target_id: int,
) -> bool:
    src = (
        await session.execute(
            text(
                "SELECT id, alias_normalized, locale FROM category_aliases "
                "WHERE category_id = :sid AND alias = :alias LIMIT 1"
            ),
            {"sid": source_id, "alias": alias_text},
        )
    ).mappings().first()
    if src is None:
        return False
    conflict = (
        await session.execute(
            text(
                "SELECT id FROM category_aliases "
                "WHERE category_id = :tid AND alias_normalized = :norm AND locale = :loc LIMIT 1"
            ),
            {"tid": target_id, "norm": src["alias_normalized"], "loc": src["locale"]},
        )
    ).first()
    if conflict:
        await session.execute(
            text("UPDATE category_aliases SET is_enabled = false WHERE id = :id"),
            {"id": src["id"]},
        )
        return False
    await session.execute(
        text(
            "UPDATE category_aliases SET category_id = :tid, is_enabled = true WHERE id = :id"
        ),
        {"tid": target_id, "id": src["id"]},
    )
    return True


async def _move_all_aliases(session: AsyncSession, *, source_id: int, target_id: int) -> int:
    rows = (
        await session.execute(
            text("SELECT id, alias_normalized, locale FROM category_aliases WHERE category_id = :sid"),
            {"sid": source_id},
        )
    ).mappings().all()
    moved = 0
    for row in rows:
        conflict = (
            await session.execute(
                text(
                    "SELECT id FROM category_aliases "
                    "WHERE category_id = :tid AND alias_normalized = :norm AND locale = :loc LIMIT 1"
                ),
                {"tid": target_id, "norm": row["alias_normalized"], "loc": row["locale"]},
            )
        ).first()
        if conflict:
            await session.execute(
                text("UPDATE category_aliases SET is_enabled = false WHERE id = :id"),
                {"id": row["id"]},
            )
            continue
        await session.execute(
            text(
                "UPDATE category_aliases SET category_id = :tid, is_enabled = true WHERE id = :id"
            ),
            {"tid": target_id, "id": row["id"]},
        )
        moved += 1
    return moved


async def migrate_intelligence(session: AsyncSession) -> tuple[int, int, int]:
    slug_ids = await _slug_id_map(session)
    filters_migrated = 0
    aliases_migrated = 0
    core_migrated = 0

    filters_migrated += await _copy_filters_sql(
        session,
        source_id=slug_ids["transport-cars"],
        target_id=slug_ids["transport-car-sale"],
    )
    aliases_migrated += await _move_all_aliases(
        session,
        source_id=slug_ids["transport-cars"],
        target_id=slug_ids["transport-car-sale"],
    )

    core_migrated += await _copy_core_sql(
        session,
        source_id=slug_ids["transport-parts"],
        target_id=slug_ids["transport-auto-parts"],
    )
    for alias_text, target_slug in PARTS_ALIAS_TO_CANONICAL_SLUG.items():
        if await _move_alias(
            session,
            alias_text=alias_text,
            source_id=slug_ids["transport-parts"],
            target_id=slug_ids[target_slug],
        ):
            aliases_migrated += 1

    for target_slug in ("transport-cargo", "transport-special-equipment"):
        core_migrated += await _copy_core_sql(
            session,
            source_id=slug_ids["transport-trucks"],
            target_id=slug_ids[target_slug],
        )
    for alias_text, target_slug in TRUCKS_ALIAS_TO_CANONICAL_SLUG.items():
        if await _move_alias(
            session,
            alias_text=alias_text,
            source_id=slug_ids["transport-trucks"],
            target_id=slug_ids[target_slug],
        ):
            aliases_migrated += 1

    core_migrated += await _copy_core_sql(
        session,
        source_id=slug_ids["transport-moto"],
        target_id=slug_ids["transport-moto-tech"],
    )
    aliases_migrated += await _move_all_aliases(
        session,
        source_id=slug_ids["transport-moto"],
        target_id=slug_ids["transport-moto-tech"],
    )

    core_migrated += await _copy_core_sql(
        session,
        source_id=slug_ids["transport-water"],
        target_id=slug_ids["transport-watercraft"],
    )
    aliases_migrated += await _move_all_aliases(
        session,
        source_id=slug_ids["transport-water"],
        target_id=slug_ids["transport-watercraft"],
    )

    return filters_migrated, aliases_migrated, core_migrated


async def update_routing_rules(session: AsyncSession) -> int:
    result = await session.execute(
        text(
            "UPDATE category_ai_rules "
            "SET config = jsonb_set(config, '{target_category_slug}', '\"transport-cargo\"') "
            "WHERE name = 'kamaz_sale' AND config->>'target_category_slug' = 'transport-trucks'"
        )
    )
    return result.rowcount or 0


async def remap_ai_search_tasks(session: AsyncSession) -> int:
    legacy_set = set(LEGACY_TRANSPORT_IDS)
    changed = 0
    rows = (
        await session.execute(
            text("SELECT id, category_ids FROM ai_search_tasks WHERE category_ids::text != '[]'")
        )
    ).all()
    for row in rows:
        task_id = row.id
        ids: list[int] = list(row.category_ids or [])
        new_ids: list[int] = []
        seen: set[int] = set()
        modified = False
        for cid in ids:
            if cid in legacy_set:
                if cid in (607, 608):
                    modified = True
                    continue
                replacement = AI_SEARCH_TASK_LEGACY_ID_REMAP.get(cid)
                if replacement is not None:
                    cid = replacement
                    modified = True
            if cid not in seen:
                new_ids.append(cid)
                seen.add(cid)
        if modified:
            await session.execute(
                text(
                    "UPDATE ai_search_tasks SET category_ids = CAST(:ids AS jsonb) WHERE id = :id"
                ),
                {"ids": json.dumps(new_ids), "id": task_id},
            )
            changed += 1
    return changed


async def deactivate_legacy_transport(session: AsyncSession) -> list[int]:
    deactivated: list[int] = []
    for legacy_id in LEGACY_TRANSPORT_IDS:
        row = (
            await session.execute(
                text("SELECT is_active FROM categories WHERE id = :id"),
                {"id": legacy_id},
            )
        ).first()
        if row and row.is_active:
            await session.execute(
                text("UPDATE categories SET is_active = false WHERE id = :id"),
                {"id": legacy_id},
            )
            deactivated.append(legacy_id)
    return deactivated


async def verify_post_migration(session: AsyncSession) -> dict[str, Any]:
    slug_ids = await _slug_id_map(session)
    stats: dict[str, Any] = {}

    stats["categories_total"] = (
        await session.execute(text("SELECT COUNT(*) FROM categories"))
    ).scalar_one()
    stats["categories_active"] = (
        await session.execute(text("SELECT COUNT(*) FROM categories WHERE is_active = true"))
    ).scalar_one()
    stats["categories_inactive"] = (
        await session.execute(text("SELECT COUNT(*) FROM categories WHERE is_active = false"))
    ).scalar_one()

    for legacy_id in LEGACY_TRANSPORT_IDS:
        active = (
            await session.execute(
                text("SELECT is_active FROM categories WHERE id = :id"),
                {"id": legacy_id},
            )
        ).scalar_one()
        stats[f"legacy_{legacy_id}_active"] = bool(active)

    car_sale_id = slug_ids["transport-car-sale"]
    stats["car_sale_filters"] = (
        await session.execute(
            text("SELECT COUNT(*) FROM category_filters WHERE category_id = :id"),
            {"id": car_sale_id},
        )
    ).scalar_one()
    stats["car_sale_aliases"] = (
        await session.execute(
            text(
                "SELECT COUNT(*) FROM category_aliases "
                "WHERE category_id = :id AND is_enabled = true"
            ),
            {"id": car_sale_id},
        )
    ).scalar_one()
    stats["car_sale_core"] = (
        await session.execute(
            text("SELECT COUNT(*) FROM category_core_fields WHERE category_id = :id"),
            {"id": car_sale_id},
        )
    ).scalar_one()
    stats["car_sale_optional"] = (
        await session.execute(
            text("SELECT COUNT(*) FROM category_optional_fields WHERE category_id = :id"),
            {"id": car_sale_id},
        )
    ).scalar_one()
    stats["transport_l2_active"] = (
        await session.execute(
            text("SELECT COUNT(*) FROM categories WHERE parent_id = :pid AND is_active = true"),
            {"pid": slug_ids["transport"]},
        )
    ).scalar_one()
    stats["car_sale_listings"] = (
        await session.execute(
            text("SELECT COUNT(*) FROM listings WHERE category_id = :id"),
            {"id": car_sale_id},
        )
    ).scalar_one()
    rule = (
        await session.execute(
            text("SELECT config FROM category_ai_rules WHERE name = 'kamaz_sale' LIMIT 1")
        )
    ).scalar_one_or_none()
    stats["kamaz_sale_target"] = (rule or {}).get("target_category_slug") if rule else None

    legacy_active_slugs = (
        await session.execute(
            text(
                "SELECT slug FROM categories WHERE id = ANY(:ids) AND is_active = true"
            ),
            {"ids": list(LEGACY_TRANSPORT_IDS)},
        )
    ).scalars().all()
    stats["legacy_transport_still_active"] = list(legacy_active_slugs)

    return stats


def load_canonical_map() -> dict[str, Any]:
    return json.loads(CANONICAL_MAP_V1_PATH.read_text(encoding="utf-8"))


async def run_phase1_migration(session: AsyncSession) -> MigrationResult:
    pf = await preflight(session)
    if not pf.ok:
        raise RuntimeError(f"Preflight failed: {pf.errors}")

    snapshot_path, digest = await create_rollback_snapshot(session)

    filters_migrated, aliases_migrated, core_migrated = await migrate_intelligence(session)
    routing_updated = await update_routing_rules(session)
    ai_updated = await remap_ai_search_tasks(session)
    deactivated = await deactivate_legacy_transport(session)

    await session.commit()

    return MigrationResult(
        snapshot_path=str(snapshot_path),
        snapshot_sha256=digest,
        filters_migrated=filters_migrated,
        aliases_migrated=aliases_migrated,
        core_migrated=core_migrated,
        routing_rules_updated=routing_updated,
        ai_tasks_updated=ai_updated,
        legacy_deactivated=deactivated,
    )


RETIRED_TRANSPORT_SLUGS_FOR_ROUTING = RETIRED_TRANSPORT_SLUGS
