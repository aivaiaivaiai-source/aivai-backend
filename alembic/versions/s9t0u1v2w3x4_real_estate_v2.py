"""Real Estate V2: property-leaf SoT; retire deal dual-tree.

Revision ID: s9t0u1v2w3x4realestatev2
Revises: r8s9t0u1v2w3pickerparent
Create Date: 2026-11-05

- Keep 601 real-estate as picker-only root (clear schema)
- Canonical property leaves: 863/864/866/867/868 + 869 Garages + new Parking
- Retire legacy deal homes 602/603/604 (inactive; preserve IDs)
- Retire unused skeletons 865/870/871/872 (inactive)
- Split 869 «Гаражи и парковки» → Гаражи; create Парковки
- Seed leaf core_fields + category_filters from real_estate_v2
- Remap aliases off retired deal homes onto property leaves
- Do NOT guess-remap ambiguous drafts on 601/602
"""
from __future__ import annotations

import json

from alembic import op
from sqlalchemy import text

from app.seeds.real_estate_v2 import (
    APARTMENTS_ID,
    APARTMENTS_SLUG,
    CANONICAL_LEAF_LABELS,
    CANONICAL_LEAF_SORT,
    COMMERCIAL_ID,
    COMMERCIAL_SLUG,
    GARAGES_ID,
    GARAGES_LABEL,
    GARAGES_SLUG,
    HOUSES_ID,
    HOUSES_SLUG,
    LAND_ID,
    LAND_SLUG,
    LEGACY_DEAL_IDS,
    PARKING_LABEL,
    PARKING_SLUG,
    RE_ALIASES,
    RE_CORE_FIELDS_BY_SLUG,
    RE_SEARCH_FILTERS_BY_SLUG,
    RETIRED_SKELETON_IDS,
    ROOMS_ID,
    ROOMS_SLUG,
    ROOT_ID,
    ROOT_SLUG,
)

revision = "s9t0u1v2w3x4realestatev2"
down_revision = "r8s9t0u1v2w3pickerparent"
branch_labels = None
depends_on = None


def _upsert_alias(bind, alias: str, target_slug: str, *, weight: int = 100) -> None:
    target = bind.execute(
        text("SELECT id FROM categories WHERE slug = :s"),
        {"s": target_slug},
    ).fetchone()
    if target is None:
        return
    cid = int(target[0])
    existing = bind.execute(
        text(
            """
            SELECT id FROM category_aliases
            WHERE alias_normalized = :a AND locale = 'ru'
            LIMIT 1
            """
        ),
        {"a": alias},
    ).fetchone()
    if existing is not None:
        bind.execute(
            text(
                """
                UPDATE category_aliases
                SET category_id = :cid,
                    alias = :alias,
                    is_enabled = true,
                    weight = :w,
                    updated_at = now()
                WHERE id = :id
                """
            ),
            {"cid": cid, "alias": alias, "w": weight, "id": int(existing[0])},
        )
    else:
        bind.execute(
            text(
                """
                INSERT INTO category_aliases
                (category_id, alias, alias_normalized, alias_compact, locale,
                 weight, is_enabled, created_at, updated_at)
                VALUES
                (:cid, :alias, :alias, :alias, 'ru',
                 :w, true, now(), now())
                """
            ),
            {"cid": cid, "alias": alias, "w": weight},
        )


def _replace_core_fields(bind, category_id: int, fields: list) -> None:
    bind.execute(
        text("DELETE FROM category_core_fields WHERE category_id = :cid"),
        {"cid": category_id},
    )
    for field in fields:
        key, label, ftype, required, sort, options, hint = field
        bind.execute(
            text(
                """
                INSERT INTO category_core_fields
                (category_id, field_key, label, field_type, is_required,
                 sort_order, options, ai_hint, create_intent, created_at, updated_at)
                VALUES
                (:cid, :key, :label, CAST(:ftype AS category_field_type_enum),
                 :req, :sort, CAST(:opts AS jsonb), :hint, NULL, now(), now())
                """
            ),
            {
                "cid": category_id,
                "key": key,
                "label": label,
                "ftype": ftype.value if hasattr(ftype, "value") else str(ftype),
                "req": required,
                "sort": sort,
                "opts": json.dumps(options, ensure_ascii=False) if options is not None else None,
                "hint": hint,
            },
        )


def _replace_filters(bind, category_id: int, filters: list) -> None:
    bind.execute(
        text("DELETE FROM category_filters WHERE category_id = :cid"),
        {"cid": category_id},
    )
    for filt in filters:
        key, label, ftype, sort, config = filt
        bind.execute(
            text(
                """
                INSERT INTO category_filters
                (category_id, filter_key, label, filter_type, sort_order,
                 config, search_intent, created_at, updated_at)
                VALUES
                (:cid, :key, :label, CAST(:ftype AS category_filter_type_enum),
                 :sort, CAST(:cfg AS jsonb), '', now(), now())
                """
            ),
            {
                "cid": category_id,
                "key": key,
                "label": label,
                "ftype": ftype.value if hasattr(ftype, "value") else str(ftype),
                "sort": sort,
                "cfg": json.dumps(config or {}, ensure_ascii=False),
            },
        )


def _clear_schema(bind, category_id: int) -> None:
    for table in (
        "category_core_fields",
        "category_optional_fields",
        "category_filters",
    ):
        bind.execute(
            text(f"DELETE FROM {table} WHERE category_id = :cid"),
            {"cid": category_id},
        )


def upgrade() -> None:
    bind = op.get_bind()

    root = bind.execute(
        text("SELECT id, slug FROM categories WHERE id = :id OR slug = :s"),
        {"id": ROOT_ID, "s": ROOT_SLUG},
    ).fetchone()
    if root is None:
        raise RuntimeError("Missing Real Estate root 601/real-estate")
    root_id = int(root[0])

    # Pre-migration listing counts (report only; no destructive remap of ambiguous drafts).
    for check_id in (ROOT_ID, *LEGACY_DEAL_IDS, *RETIRED_SKELETON_IDS, GARAGES_ID):
        n = bind.execute(
            text(
                """
                SELECT status, COUNT(*) FROM listings
                WHERE category_id = :id GROUP BY status
                """
            ),
            {"id": check_id},
        ).fetchall()
        _ = n

    # Root: active picker-only.
    bind.execute(
        text(
            """
            UPDATE categories
            SET is_active = true, parent_id = NULL, name = 'Недвижимость',
                slug = :slug, updated_at = now()
            WHERE id = :id
            """
        ),
        {"id": root_id, "slug": ROOT_SLUG},
    )
    _clear_schema(bind, root_id)

    leaf_specs = [
        (APARTMENTS_ID, APARTMENTS_SLUG),
        (HOUSES_ID, HOUSES_SLUG),
        (ROOMS_ID, ROOMS_SLUG),
        (LAND_ID, LAND_SLUG),
        (COMMERCIAL_ID, COMMERCIAL_SLUG),
        (GARAGES_ID, GARAGES_SLUG),
    ]
    for cid, slug in leaf_specs:
        row = bind.execute(
            text("SELECT id FROM categories WHERE id = :id"),
            {"id": cid},
        ).fetchone()
        if row is None:
            raise RuntimeError(f"Missing Real Estate leaf id={cid} for {slug}")
        bind.execute(
            text(
                """
                UPDATE categories
                SET parent_id = :pid,
                    slug = :slug,
                    name = :label,
                    is_active = true,
                    sort_order = :sort,
                    updated_at = now()
                WHERE id = :id
                """
            ),
            {
                "pid": root_id,
                "slug": slug,
                "label": CANONICAL_LEAF_LABELS[slug]
                if slug != GARAGES_SLUG
                else GARAGES_LABEL,
                "sort": CANONICAL_LEAF_SORT[slug],
                "id": cid,
            },
        )

    # Parking leaf (new).
    parking = bind.execute(
        text("SELECT id FROM categories WHERE slug = :s"),
        {"s": PARKING_SLUG},
    ).fetchone()
    if parking is None:
        bind.execute(
            text(
                """
                INSERT INTO categories
                (name, slug, parent_id, entity_type, sort_order, is_active,
                 requires_city, created_at, updated_at)
                VALUES
                (:name, :slug, :pid, CAST('object' AS category_entity_type_enum),
                 :sort, true, false, now(), now())
                """
            ),
            {
                "name": PARKING_LABEL,
                "slug": PARKING_SLUG,
                "pid": root_id,
                "sort": CANONICAL_LEAF_SORT[PARKING_SLUG],
            },
        )
    else:
        bind.execute(
            text(
                """
                UPDATE categories
                SET parent_id = :pid, name = :name, is_active = true,
                    sort_order = :sort, updated_at = now()
                WHERE id = :id
                """
            ),
            {
                "pid": root_id,
                "name": PARKING_LABEL,
                "sort": CANONICAL_LEAF_SORT[PARKING_SLUG],
                "id": int(parking[0]),
            },
        )

    # Retire legacy deal homes + unused skeletons (preserve identity; clear schema).
    for rid in (*LEGACY_DEAL_IDS, *RETIRED_SKELETON_IDS):
        bind.execute(
            text(
                """
                UPDATE categories
                SET is_active = false, updated_at = now()
                WHERE id = :id
                """
            ),
            {"id": rid},
        )
        _clear_schema(bind, rid)

    # Seed schemas on canonical leaves.
    for slug, fields in RE_CORE_FIELDS_BY_SLUG.items():
        row = bind.execute(
            text("SELECT id FROM categories WHERE slug = :s"),
            {"s": slug},
        ).fetchone()
        if row is None:
            continue
        cid = int(row[0])
        bind.execute(
            text("DELETE FROM category_optional_fields WHERE category_id = :cid"),
            {"cid": cid},
        )
        _replace_core_fields(bind, cid, fields)
        _replace_filters(bind, cid, RE_SEARCH_FILTERS_BY_SLUG.get(slug, []))

    # Remap aliases that still point at retired deal homes → apartments (safe default for
    # apartment-ish phrases) or commercial; RE_ALIASES below sets precise targets.
    for deal_id, fallback_slug in (
        (602, APARTMENTS_SLUG),
        (603, APARTMENTS_SLUG),
        (604, COMMERCIAL_SLUG),
    ):
        bind.execute(
            text(
                """
                UPDATE category_aliases a
                SET category_id = c.id, updated_at = now()
                FROM categories c
                WHERE a.category_id = :deal_id
                  AND c.slug = :slug
                """
            ),
            {"deal_id": deal_id, "slug": fallback_slug},
        )

    for alias, target_slug, weight in RE_ALIASES:
        _upsert_alias(bind, alias, target_slug, weight=weight)


def downgrade() -> None:
    # Non-destructive: do not restore competing deal taxonomy as live SoT.
    pass
