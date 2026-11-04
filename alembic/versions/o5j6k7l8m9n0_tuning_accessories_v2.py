"""Transport Tuning & Accessories V2: 13 sections + product_type SoT.

Revision ID: o5j6k7l8m9n0tuningaccv2
Revises: n4i5j6k7l8m9currencyv2
Create Date: 2026-11-03
"""
from __future__ import annotations

import json

from alembic import op
from sqlalchemy import text

from app.seeds.tuning_accessories_v2 import (
    AUDIO_ID,
    AUDIO_LEGACY_SLUG,
    AUDIO_SLUG,
    KIDS_BOUNDARY_ALIASES,
    LEAF_ALIASES,
    LEAF_IDS,
    LEAF_LABELS,
    LEAF_SLUGS,
    LEAF_SORT,
    PARENT_ALIASES,
    PARENT_ID,
    PARENT_LABEL,
    PARENT_SLUG,
    PARTS_BOUNDARY_ALIASES,
    RETIRE_OR_HIDE_IDS,
    SERVICE_BOUNDARY_ALIASES,
    TECHNICAL_ID,
    TECHNICAL_LEGACY_SLUG,
    TECHNICAL_SLUG,
    TUNING_CORE_FIELDS_BY_SLUG,
    TUNING_SEARCH_FILTERS_BY_SLUG,
)

revision = "o5j6k7l8m9n0tuningaccv2"
down_revision = "n4i5j6k7l8m9currencyv2"
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
            {
                "cid": cid,
                "alias": alias,
                "w": weight,
                "id": int(existing[0]),
            },
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
                "opts": json.dumps(options) if options is not None else None,
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
                "cfg": json.dumps(config or {}),
            },
        )


def _ensure_leaf(
    bind,
    *,
    leaf_id: int,
    slug: str,
    name: str,
    parent_id: int,
    sort_order: int,
) -> None:
    row = bind.execute(
        text("SELECT id, slug FROM categories WHERE id = :id"),
        {"id": leaf_id},
    ).fetchone()
    if row is None:
        bind.execute(
            text(
                """
                INSERT INTO categories
                (id, parent_id, slug, name, entity_type, is_active, sort_order,
                 created_at, updated_at)
                VALUES
                (:id, :pid, :slug, :name,
                 CAST('object' AS category_entity_type_enum),
                 true, :sort, now(), now())
                """
            ),
            {
                "id": leaf_id,
                "pid": parent_id,
                "slug": slug,
                "name": name,
                "sort": sort_order,
            },
        )
        bind.execute(
            text(
                """
                SELECT setval(
                  pg_get_serial_sequence('categories', 'id'),
                  GREATEST((SELECT MAX(id) FROM categories), :id)
                )
                """
            ),
            {"id": leaf_id},
        )
        return
    bind.execute(
        text(
            """
            UPDATE categories
            SET parent_id = :pid,
                slug = :slug,
                name = :name,
                is_active = true,
                sort_order = :sort,
                updated_at = now()
            WHERE id = :id
            """
        ),
        {
            "pid": parent_id,
            "slug": slug,
            "name": name,
            "sort": sort_order,
            "id": leaf_id,
        },
    )


def upgrade() -> None:
    bind = op.get_bind()

    parent = bind.execute(
        text("SELECT id FROM categories WHERE slug = :s"),
        {"s": PARENT_SLUG},
    ).fetchone()
    if parent is None:
        raise RuntimeError(f"Missing parent {PARENT_SLUG}")
    parent_id = int(parent[0])
    if parent_id != PARENT_ID:
        raise RuntimeError(f"Parent expected id={PARENT_ID}, got {parent_id}")

    # Pre-mutation safety: refuse silent identity reuse if listings appeared.
    for cid in (PARENT_ID, *LEAF_IDS.values(), *RETIRE_OR_HIDE_IDS):
        n = bind.execute(
            text("SELECT COUNT(*) FROM listings WHERE category_id = :id"),
            {"id": cid},
        ).scalar()
        if int(n or 0) > 0 and cid in (
            AUDIO_ID,
            TECHNICAL_ID,
            *RETIRE_OR_HIDE_IDS,
        ):
            # Audio/technical slug rename + retire nodes: block if live data.
            raise RuntimeError(
                f"category_id={cid} has {n} listings — reconcile before Tuning V2"
            )

    bind.execute(
        text(
            """
            UPDATE categories
            SET is_active = true,
                name = :name,
                updated_at = now()
            WHERE id = :pid
            """
        ),
        {"pid": parent_id, "name": PARENT_LABEL},
    )

    # Rename Audio legacy slug → avtozvuk (ID 725 preserved).
    bind.execute(
        text(
            """
            UPDATE categories
            SET slug = :new_slug,
                name = :name,
                is_active = true,
                sort_order = :sort,
                parent_id = :pid,
                updated_at = now()
            WHERE id = :id OR slug = :legacy
            """
        ),
        {
            "new_slug": AUDIO_SLUG,
            "name": LEAF_LABELS[AUDIO_SLUG],
            "sort": LEAF_SORT[AUDIO_SLUG],
            "pid": parent_id,
            "id": AUDIO_ID,
            "legacy": AUDIO_LEGACY_SLUG,
        },
    )

    # Rename Technical legacy sportivnyy → tehnicheskiy (ID 732).
    bind.execute(
        text(
            """
            UPDATE categories
            SET slug = :new_slug,
                name = :name,
                is_active = true,
                sort_order = :sort,
                parent_id = :pid,
                updated_at = now()
            WHERE id = :id OR slug = :legacy
            """
        ),
        {
            "new_slug": TECHNICAL_SLUG,
            "name": LEAF_LABELS[TECHNICAL_SLUG],
            "sort": LEAF_SORT[TECHNICAL_SLUG],
            "pid": parent_id,
            "id": TECHNICAL_ID,
            "legacy": TECHNICAL_LEGACY_SLUG,
        },
    )

    for slug in LEAF_SLUGS:
        _ensure_leaf(
            bind,
            leaf_id=LEAF_IDS[slug],
            slug=slug,
            name=LEAF_LABELS[slug],
            parent_id=parent_id,
            sort_order=LEAF_SORT[slug],
        )

    # Deactivate competing / non-ordinary-picker children.
    allowed = set(LEAF_IDS.values())
    extras = bind.execute(
        text(
            """
            SELECT id, slug FROM categories
            WHERE parent_id = :pid AND is_active = true
            """
        ),
        {"pid": parent_id},
    ).fetchall()
    for row in extras:
        if int(row[0]) not in allowed:
            bind.execute(
                text(
                    """
                    UPDATE categories
                    SET is_active = false, updated_at = now()
                    WHERE id = :id
                    """
                ),
                {"id": int(row[0])},
            )

    for rid in RETIRE_OR_HIDE_IDS:
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

    # Parent must not be live Create/Search SoT.
    bind.execute(
        text("DELETE FROM category_core_fields WHERE category_id = :cid"),
        {"cid": parent_id},
    )
    bind.execute(
        text("DELETE FROM category_optional_fields WHERE category_id = :cid"),
        {"cid": parent_id},
    )
    bind.execute(
        text("DELETE FROM category_filters WHERE category_id = :cid"),
        {"cid": parent_id},
    )

    managed = [parent_id, *LEAF_IDS.values()]
    for cid in managed:
        bind.execute(
            text("DELETE FROM category_optional_fields WHERE category_id = :cid"),
            {"cid": cid},
        )

    for slug, fields in TUNING_CORE_FIELDS_BY_SLUG.items():
        row = bind.execute(
            text("SELECT id FROM categories WHERE slug = :s"),
            {"s": slug},
        ).fetchone()
        if row is None:
            continue
        cid = int(row[0])
        _replace_core_fields(bind, cid, fields)
        _replace_filters(bind, cid, TUNING_SEARCH_FILTERS_BY_SLUG.get(slug, []))

    # Demote bare generic «led» from blind OEM Optics if present — aftermarket
    # phrases get higher-weight Tuning Lighting aliases below.
    for alias, leaf_slug in LEAF_ALIASES.items():
        _upsert_alias(bind, alias, leaf_slug, weight=110)
    for alias, parent_slug in PARENT_ALIASES.items():
        _upsert_alias(bind, alias, parent_slug, weight=80)
    for alias, target_slug in SERVICE_BOUNDARY_ALIASES.items():
        _upsert_alias(bind, alias, target_slug, weight=140)
    for alias, target_slug in PARTS_BOUNDARY_ALIASES.items():
        _upsert_alias(bind, alias, target_slug, weight=120)
    for alias, target_slug in KIDS_BOUNDARY_ALIASES.items():
        _upsert_alias(bind, alias, target_slug, weight=130)

    # Keep bare «коврик» on Home/Garden — do not overwrite.
    # Automotive phrases already mapped above.

    # Demote bare ambiguous «led» → OEM Optics (prefer contextual aftermarket aliases).
    led = bind.execute(
        text(
            """
            SELECT id FROM category_aliases
            WHERE alias_normalized = 'led' AND locale = 'ru'
            LIMIT 1
            """
        )
    ).fetchone()
    if led is not None:
        bind.execute(
            text(
                """
                UPDATE category_aliases
                SET is_enabled = false, weight = 10, updated_at = now()
                WHERE id = :id
                """
            ),
            {"id": int(led[0])},
        )


def downgrade() -> None:
    pass
