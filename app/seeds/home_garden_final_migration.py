# -*- coding: utf-8 -*-
"""Home & Garden FINAL catalog migration — idempotent via AsyncSession."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.seeds.home_garden_catalog_final import (
    HOME_GARDEN_LEAF_SLUGS,
    HOME_GARDEN_L2_SLUGS,
    HOME_GARDEN_NODES,
    HOME_GARDEN_ROOT_SLUG,
)
from app.seeds.home_garden_filters import (
    HOME_GARDEN_FINAL_ALIAS_REMAP,
    LEGACY_L3_REMAP,
    build_home_garden_core_fields,
    build_home_garden_search_filters,
)
from app.services.category_text import normalize_alias_keys

logger = logging.getLogger(__name__)

MIGRATION_MARKER = "__home_garden_final_v2_filters__"


@dataclass
class MigrationResult:
    created: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    retired: list[str] = field(default_factory=list)
    listings_remapped: int = 0
    aliases_upserted: int = 0
    fields_upserted: int = 0
    filters_upserted: int = 0
    already_applied: bool = False
    dry_run: bool = False


async def _slug_map(session: AsyncSession) -> dict[str, dict[str, Any]]:
    rows = (
        await session.execute(
            text(
                "SELECT id, slug, name, parent_id, is_active, sort_order "
                "FROM categories"
            )
        )
    ).mappings().all()
    return {r["slug"]: dict(r) for r in rows}


async def run_home_garden_final_migration(
    session: AsyncSession,
    *,
    dry_run: bool = False,
) -> MigrationResult:
    result = MigrationResult(dry_run=dry_run)
    slugs = await _slug_map(session)

    if HOME_GARDEN_ROOT_SLUG not in slugs:
        raise RuntimeError("home-garden root missing")

    marker = (
        await session.execute(
            text(
                "SELECT 1 FROM category_aliases WHERE alias = :a AND locale = 'ru' LIMIT 1"
            ),
            {"a": MIGRATION_MARKER},
        )
    ).scalar_one_or_none()
    result.already_applied = bool(marker)

    target_slugs = {s for _p, s, _n, _so, _d in HOME_GARDEN_NODES}
    now = datetime.now(UTC).replace(tzinfo=None)

    # 1) Upsert TARGET nodes parent-first (nodes list is already parent-before-child).
    for parent_slug, slug, name, sort_order, _depth in HOME_GARDEN_NODES:
        parent = slugs.get(parent_slug)
        if parent is None:
            raise RuntimeError(f"missing parent {parent_slug} for {slug}")
        parent_id = int(parent["id"])
        existing = slugs.get(slug)
        if existing is None:
            if not dry_run:
                row = (
                    await session.execute(
                        text(
                            """
                            INSERT INTO categories
                              (slug, name, entity_type, sort_order, parent_id,
                               is_active, requires_city, created_at, updated_at)
                            VALUES
                              (:slug, :name, 'object', :sort_order, :parent_id,
                               true, true, :now, :now)
                            RETURNING id
                            """
                        ),
                        {
                            "slug": slug,
                            "name": name,
                            "sort_order": sort_order,
                            "parent_id": parent_id,
                            "now": now,
                        },
                    )
                ).mappings().one()
                new_id = int(row["id"])
            else:
                new_id = -abs(hash(slug)) % 2_000_000_000
            slugs[slug] = {
                "id": new_id,
                "slug": slug,
                "name": name,
                "parent_id": parent_id,
                "is_active": True,
                "sort_order": sort_order,
            }
            result.created.append(slug)
        else:
            if not dry_run:
                await session.execute(
                    text(
                        """
                        UPDATE categories
                        SET name = :name,
                            parent_id = :parent_id,
                            sort_order = :sort_order,
                            is_active = true,
                            updated_at = :now
                        WHERE id = :id
                        """
                    ),
                    {
                        "name": name,
                        "parent_id": parent_id,
                        "sort_order": sort_order,
                        "now": now,
                        "id": int(existing["id"]),
                    },
                )
            result.updated.append(slug)

    slugs = await _slug_map(session) if not dry_run else slugs

    # 2) Remap listings from legacy L3 → TARGET
    for old_slug, new_slug in LEGACY_L3_REMAP.items():
        if old_slug == new_slug:
            continue
        old = slugs.get(old_slug)
        new = slugs.get(new_slug)
        if not old or not new:
            continue
        if dry_run:
            cnt = int(
                (
                    await session.execute(
                        text("SELECT COUNT(*) FROM listings WHERE category_id = :id"),
                        {"id": int(old["id"])},
                    )
                ).scalar_one()
            )
            result.listings_remapped += cnt
            continue
        res = await session.execute(
            text(
                """
                UPDATE listings
                SET category_id = :new_id, updated_at = :now
                WHERE category_id = :old_id
                """
            ),
            {"new_id": int(new["id"]), "old_id": int(old["id"]), "now": now},
        )
        result.listings_remapped += res.rowcount or 0

    # 3) Retire active home-garden descendants not in TARGET (keep L1 root + TARGET)
    # Collect all descendants of home-garden.
    root_id = int(slugs[HOME_GARDEN_ROOT_SLUG]["id"])
    by_parent: dict[int | None, list[dict[str, Any]]] = {}
    for row in slugs.values():
        by_parent.setdefault(row["parent_id"], []).append(row)

    def walk(pid: int) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for ch in by_parent.get(pid, []):
            out.append(ch)
            out.extend(walk(int(ch["id"])))
        return out

    for row in walk(root_id):
        slug = row["slug"]
        if slug in target_slugs:
            continue
        if slug in HOME_GARDEN_L2_SLUGS:
            continue
        if not row["is_active"]:
            continue
        # Keep L2 that somehow aren't in NODES? All L2 are in NODES.
        if not dry_run:
            await session.execute(
                text(
                    """
                    UPDATE categories
                    SET is_active = false, updated_at = :now
                    WHERE id = :id
                    """
                ),
                {"id": int(row["id"]), "now": now},
            )
            await session.execute(
                text(
                    """
                    UPDATE category_aliases
                    SET is_enabled = false
                    WHERE category_id = :id
                    """
                ),
                {"id": int(row["id"])},
            )
        result.retired.append(slug)

    # 4) Leaf core fields (replace set for each leaf)
    leaf_fields = build_home_garden_core_fields()
    for leaf_slug, fields in leaf_fields.items():
        cat = slugs.get(leaf_slug)
        if not cat:
            continue
        cat_id = int(cat["id"])
        if not dry_run:
            await session.execute(
                text("DELETE FROM category_core_fields WHERE category_id = :cid"),
                {"cid": cat_id},
            )
        for sort_i, (key, label, ftype, required, options, hint) in enumerate(fields):
            if key in {"city", "price", "title", "description", "photos"}:
                continue
            opts_json = json.dumps(options, ensure_ascii=False) if options else None
            if dry_run:
                result.fields_upserted += 1
                continue
            existing = (
                await session.execute(
                    text(
                        """
                        SELECT id FROM category_core_fields
                        WHERE category_id = :cid AND field_key = :key
                        """
                    ),
                    {"cid": cat_id, "key": key},
                )
            ).scalar_one_or_none()
            if existing is None:
                await session.execute(
                    text(
                        """
                        INSERT INTO category_core_fields
                          (category_id, field_key, label, field_type, is_required,
                           sort_order, options, ai_hint, created_at, updated_at)
                        VALUES
                          (:cid, :key, :label, :ftype, :req,
                           :sort, CAST(:opts AS jsonb), :hint, :now, :now)
                        """
                    ),
                    {
                        "cid": cat_id,
                        "key": key,
                        "label": label,
                        "ftype": ftype.value if hasattr(ftype, "value") else ftype,
                        "req": required,
                        "sort": sort_i,
                        "opts": opts_json,
                        "hint": hint,
                        "now": now,
                    },
                )
            else:
                await session.execute(
                    text(
                        """
                        UPDATE category_core_fields
                        SET label = :label,
                            field_type = :ftype,
                            is_required = :req,
                            sort_order = :sort,
                            options = CAST(:opts AS jsonb),
                            ai_hint = :hint,
                            updated_at = :now
                        WHERE id = :id
                        """
                    ),
                    {
                        "label": label,
                        "ftype": ftype.value if hasattr(ftype, "value") else ftype,
                        "req": required,
                        "sort": sort_i,
                        "opts": opts_json,
                        "hint": hint,
                        "now": now,
                        "id": int(existing),
                    },
                )
            result.fields_upserted += 1

    # 5) Strip city/price/item_type from L2 (common fields live on listing form)
    for l2 in HOME_GARDEN_L2_SLUGS:
        cat = slugs.get(l2)
        if not cat:
            continue
        if dry_run:
            continue
        await session.execute(
            text(
                """
                DELETE FROM category_core_fields
                WHERE category_id = :cid
                  AND field_key IN ('city', 'price', 'title', 'description', 'photos', 'item_type')
                """
            ),
            {"cid": int(cat["id"])},
        )

    # 5b) Search filters for Home & Garden leaves (subset of core keys)
    leaf_search = build_home_garden_search_filters()
    for leaf_slug, filters in leaf_search.items():
        cat = slugs.get(leaf_slug)
        if not cat:
            continue
        cat_id = int(cat["id"])
        if not dry_run:
            await session.execute(
                text("DELETE FROM category_filters WHERE category_id = :cid"),
                {"cid": cat_id},
            )
        for sort_i, (key, label, ftype, config) in enumerate(filters):
            if dry_run:
                result.filters_upserted += 1
                continue
            cfg_json = json.dumps(config, ensure_ascii=False) if config else None
            await session.execute(
                text(
                    """
                    INSERT INTO category_filters
                      (category_id, filter_key, label, filter_type, sort_order,
                       config, created_at, updated_at)
                    VALUES
                      (:cid, :key, :label, CAST(:ftype AS category_filter_type_enum),
                       :sort, CAST(:cfg AS jsonb), :now, :now)
                    """
                ),
                {
                    "cid": cat_id,
                    "key": key,
                    "label": label,
                    "ftype": ftype,
                    "sort": sort_i,
                    "cfg": cfg_json,
                    "now": now,
                },
            )
            result.filters_upserted += 1

    # 6) Aliases
    for alias, target_slug in HOME_GARDEN_FINAL_ALIAS_REMAP.items():
        cat = slugs.get(target_slug)
        if not cat:
            continue
        if dry_run:
            result.aliases_upserted += 1
            continue
        spaced, compact = normalize_alias_keys(alias)
        existing = (
            await session.execute(
                text(
                    """
                    SELECT id FROM category_aliases
                    WHERE locale = 'ru' AND alias_normalized = :n
                    LIMIT 1
                    """
                ),
                {"n": spaced},
            )
        ).scalar_one_or_none()
        if existing is None:
            await session.execute(
                text(
                    """
                    INSERT INTO category_aliases
                      (category_id, locale, alias, alias_normalized, alias_compact,
                       weight, is_enabled, created_at, updated_at)
                    VALUES
                      (:cid, 'ru', :alias, :norm, :compact, 100, true, :now, :now)
                    """
                ),
                {
                    "cid": int(cat["id"]),
                    "alias": alias,
                    "norm": spaced,
                    "compact": compact,
                    "now": now,
                },
            )
        else:
            await session.execute(
                text(
                    """
                    UPDATE category_aliases
                    SET category_id = :cid,
                        alias = :alias,
                        alias_compact = :compact,
                        weight = 100,
                        is_enabled = true,
                        updated_at = :now
                    WHERE id = :id
                    """
                ),
                {
                    "cid": int(cat["id"]),
                    "alias": alias,
                    "compact": compact,
                    "now": now,
                    "id": int(existing),
                },
            )
        result.aliases_upserted += 1

    # Marker alias on home-garden root (idempotent)
    if not dry_run:
        root = slugs[HOME_GARDEN_ROOT_SLUG]
        marker_exists = (
            await session.execute(
                text(
                    "SELECT 1 FROM category_aliases WHERE alias = :a AND locale = 'ru' LIMIT 1"
                ),
                {"a": MIGRATION_MARKER},
            )
        ).scalar_one_or_none()
        if marker_exists is None:
            spaced, compact = normalize_alias_keys(MIGRATION_MARKER)
            await session.execute(
                text(
                    """
                    INSERT INTO category_aliases
                      (category_id, locale, alias, alias_normalized, alias_compact,
                       weight, is_enabled, created_at, updated_at)
                    VALUES
                      (:cid, 'ru', :alias, :norm, :compact, 0, false, :now, :now)
                    """
                ),
                {
                    "cid": int(root["id"]),
                    "alias": MIGRATION_MARKER,
                    "norm": spaced,
                    "compact": compact,
                    "now": now,
                },
            )

    if not dry_run:
        await session.commit()

    logger.info(
        "home_garden_final migration created=%s updated=%s retired=%s remapped=%s fields=%s filters=%s",
        len(result.created),
        len(result.updated),
        len(result.retired),
        result.listings_remapped,
        result.fields_upserted,
        result.filters_upserted,
    )
    return result
