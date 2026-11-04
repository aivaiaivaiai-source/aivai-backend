"""Transport Auto Services V2: 10 sections + service_type SoT.

Revision ID: p6q7r8s9t0u1autosvcv2
Revises: o5j6k7l8m9n0tuningaccv2
Create Date: 2026-11-03
"""
from __future__ import annotations

import json

from alembic import op
from sqlalchemy import text

from app.seeds.auto_services_v2 import (
    AUTO_SERVICES_CORE_FIELDS_BY_SLUG,
    AUTO_SERVICES_SEARCH_FILTERS_BY_SLUG,
    CARGO_EVACUATOR_ALIASES,
    LEAF_ALIASES,
    LEAF_IDS,
    LEAF_LABELS,
    LEAF_SLUGS,
    LEAF_SORT,
    PARENT_ALIASES,
    PARENT_ID,
    PARENT_LABEL,
    PARENT_SLUG,
    TOWING_SLUG,
)

revision = "p6q7r8s9t0u1autosvcv2"
down_revision = "o5j6k7l8m9n0tuningaccv2"
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
                 CAST('service' AS category_entity_type_enum),
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

    # Pre-mutation safety — refuse silent repurpose if live data appeared.
    managed_ids = (PARENT_ID, *LEAF_IDS.values())
    for cid in managed_ids:
        n = bind.execute(
            text("SELECT COUNT(*) FROM listings WHERE category_id = :id"),
            {"id": cid},
        ).scalar()
        if int(n or 0) > 0:
            # Soft warn path: Auto Services V2 is additive schema/labels;
            # listings=0 expected from audit. Block only if field identity clash.
            fv = bind.execute(
                text(
                    """
                    SELECT COUNT(*) FROM listing_field_values lfv
                    JOIN listings l ON l.id = lfv.listing_id
                    WHERE l.category_id = :id
                    """
                ),
                {"id": cid},
            ).scalar()
            if int(fv or 0) > 0:
                raise RuntimeError(
                    f"category_id={cid} has listing field values — "
                    "reconcile before Auto Services V2"
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

    for slug in LEAF_SLUGS:
        _ensure_leaf(
            bind,
            leaf_id=LEAF_IDS[slug],
            slug=slug,
            name=LEAF_LABELS[slug],
            parent_id=parent_id,
            sort_order=LEAF_SORT[slug],
        )

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

    # Parent picker-only — no live Create/Search schema.
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

    for cid in (parent_id, *LEAF_IDS.values()):
        bind.execute(
            text("DELETE FROM category_optional_fields WHERE category_id = :cid"),
            {"cid": cid},
        )

    for slug, fields in AUTO_SERVICES_CORE_FIELDS_BY_SLUG.items():
        row = bind.execute(
            text("SELECT id FROM categories WHERE slug = :s"),
            {"s": slug},
        ).fetchone()
        if row is None:
            continue
        cid = int(row[0])
        _replace_core_fields(bind, cid, fields)
        _replace_filters(
            bind, cid, AUTO_SERVICES_SEARCH_FILTERS_BY_SLUG.get(slug, [])
        )

    for alias, leaf_slug in LEAF_ALIASES.items():
        _upsert_alias(bind, alias, leaf_slug, weight=130)
    for alias, parent_slug in PARENT_ALIASES.items():
        _upsert_alias(bind, alias, parent_slug, weight=80)
    for alias, target_slug in CARGO_EVACUATOR_ALIASES.items():
        _upsert_alias(bind, alias, target_slug, weight=150)

    # Retarget bare/service «эвакуатор» away from generic services-transport.
    _upsert_alias(bind, "эвакуатор", TOWING_SLUG, weight=140)

    # Tinting / soundproofing work → Tuning install section (not Detailing).
    _upsert_alias(
        bind,
        "тонировка автомобиля",
        "transport-auto-services-tyuning-i-doosnaschenie",
        weight=140,
    )
    _upsert_alias(
        bind,
        "тонировка авто",
        "transport-auto-services-tyuning-i-doosnaschenie",
        weight=140,
    )
    _upsert_alias(
        bind,
        "шумоизоляция автомобиля",
        "transport-auto-services-tyuning-i-doosnaschenie",
        weight=140,
    )


def downgrade() -> None:
    pass
