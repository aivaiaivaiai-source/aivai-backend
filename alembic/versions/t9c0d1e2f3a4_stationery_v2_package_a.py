"""Stationery & Books V2 Package A — Create SoT cores.

Revision ID: t9c0d1e2f3a4stationpa
Revises: s8b9c0d1e2f3stationtax
Create Date: 2026-11-12

- Seed Create cores on all 15 active Stationery L2
- Root remains picker-only (0 cores / 0 filters)
- Retired legacy leaves stay empty
- STOP if Stationery subtree has listings
- Does NOT seed Package B Search filters
"""
from __future__ import annotations

import json

from alembic import op
from sqlalchemy import text

revision = "t9c0d1e2f3a4stationpa"
down_revision = "s8b9c0d1e2f3stationtax"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from app.seeds.stationery_v2 import (
        STATIONERY_ROOT_SLUG,
        STATIONERY_V2_CANONICAL_LEAVES,
        STATIONERY_V2_CANONICAL_SLUGS,
        STATIONERY_V2_EXPECTED_L2_COUNT,
        STATIONERY_V2_RETIRED_SLUGS,
        build_stationery_v2_core_fields,
        stationery_v2_assert_package_a_contracts,
    )

    stationery_v2_assert_package_a_contracts()
    bind = op.get_bind()

    root = bind.execute(
        text("SELECT id FROM categories WHERE slug = :slug"),
        {"slug": STATIONERY_ROOT_SLUG},
    ).fetchone()
    if root is None:
        raise RuntimeError("stationery-books root missing")
    root_id = int(root[0])

    listing_n = bind.execute(
        text(
            """
            SELECT count(*) FROM listings l
            JOIN categories c ON c.id = l.category_id
            WHERE c.id = :root OR c.parent_id = :root
               OR c.slug LIKE 'stationery-books%'
               OR c.slug IN (
                 'books-fiction', 'books-study', 'books-other'
               )
            """
        ),
        {"root": root_id},
    ).scalar_one()
    if int(listing_n or 0) > 0:
        raise RuntimeError(
            f"Stationery Package A STOP: listings exist ({listing_n})"
        )

    bind.execute(
        text(
            "UPDATE categories SET is_active = true, parent_id = NULL, "
            "updated_at = now() WHERE id = :id"
        ),
        {"id": root_id},
    )
    for table in (
        "category_core_fields",
        "category_optional_fields",
        "category_filters",
    ):
        bind.execute(
            text(f"DELETE FROM {table} WHERE category_id = :cid"),
            {"cid": root_id},
        )

    slug_to_id: dict[str, int] = {}
    for label, slug, sort_order in STATIONERY_V2_CANONICAL_LEAVES:
        row = bind.execute(
            text("SELECT id FROM categories WHERE slug = :slug"),
            {"slug": slug},
        ).fetchone()
        if row is None:
            bind.execute(
                text(
                    """
                    INSERT INTO categories
                      (parent_id, slug, name, entity_type, is_active, sort_order,
                       requires_city, created_at, updated_at)
                    VALUES
                      (:pid, :slug, :name, 'object', true, :sort, true, now(), now())
                    """
                ),
                {
                    "pid": root_id,
                    "slug": slug,
                    "name": label,
                    "sort": sort_order,
                },
            )
            row = bind.execute(
                text("SELECT id FROM categories WHERE slug = :slug"),
                {"slug": slug},
            ).fetchone()
        else:
            bind.execute(
                text(
                    """
                    UPDATE categories
                    SET parent_id = :pid, name = :name, is_active = true,
                        sort_order = :sort, entity_type = 'object',
                        requires_city = true, updated_at = now()
                    WHERE id = :id
                    """
                ),
                {
                    "pid": root_id,
                    "name": label,
                    "sort": sort_order,
                    "id": int(row[0]),
                },
            )
        slug_to_id[slug] = int(row[0])

    for slug in sorted(STATIONERY_V2_RETIRED_SLUGS):
        row = bind.execute(
            text("SELECT id FROM categories WHERE slug = :slug"),
            {"slug": slug},
        ).fetchone()
        if row is None:
            continue
        cid = int(row[0])
        bind.execute(
            text(
                "UPDATE categories SET is_active = false, updated_at = now() "
                "WHERE id = :id"
            ),
            {"id": cid},
        )
        for table in (
            "category_core_fields",
            "category_optional_fields",
            "category_filters",
        ):
            bind.execute(
                text(f"DELETE FROM {table} WHERE category_id = :cid"),
                {"cid": cid},
            )

    children = bind.execute(
        text("SELECT id, slug FROM categories WHERE parent_id = :pid"),
        {"pid": root_id},
    ).fetchall()
    for cid, slug in children:
        if slug in STATIONERY_V2_CANONICAL_SLUGS:
            continue
        bind.execute(
            text(
                "UPDATE categories SET is_active = false, updated_at = now() "
                "WHERE id = :id"
            ),
            {"id": int(cid)},
        )
        for table in (
            "category_core_fields",
            "category_optional_fields",
            "category_filters",
        ):
            bind.execute(
                text(f"DELETE FROM {table} WHERE category_id = :cid"),
                {"cid": int(cid)},
            )

    def _seed_cores(cid: int, fields: list) -> None:
        for table in (
            "category_core_fields",
            "category_optional_fields",
            "category_filters",
        ):
            bind.execute(
                text(f"DELETE FROM {table} WHERE category_id = :cid"),
                {"cid": cid},
            )
        for key, label, ftype, required, sort, options, hint in fields:
            if key in {"city", "title", "description", "photos", "region"}:
                continue
            bind.execute(
                text(
                    """
                    INSERT INTO category_core_fields (
                        category_id, field_key, label, field_type, is_required,
                        sort_order, ai_hint, options, create_intent,
                        created_at, updated_at
                    ) VALUES (
                        :cid, :key, :label, :ftype, :req,
                        :sort, :hint, CAST(:options AS jsonb), NULL,
                        now(), now()
                    )
                    """
                ),
                {
                    "cid": cid,
                    "key": key,
                    "label": label,
                    "ftype": ftype.value if hasattr(ftype, "value") else str(ftype),
                    "req": bool(required),
                    "sort": int(sort),
                    "hint": hint,
                    "options": json.dumps(options, ensure_ascii=False)
                    if options
                    else None,
                },
            )

    for slug, fields in build_stationery_v2_core_fields().items():
        _seed_cores(slug_to_id[slug], fields)

    active = bind.execute(
        text(
            """
            SELECT count(*) FROM categories
            WHERE parent_id = :pid AND is_active = true
            """
        ),
        {"pid": root_id},
    ).scalar_one()
    if int(active or 0) != STATIONERY_V2_EXPECTED_L2_COUNT:
        raise RuntimeError(
            f"Stationery V2 Package A STOP: expected "
            f"{STATIONERY_V2_EXPECTED_L2_COUNT} active L2, got {active}"
        )

    nonempty = bind.execute(
        text(
            """
            SELECT count(DISTINCT c.id)
            FROM categories c
            JOIN category_core_fields cc ON cc.category_id = c.id
            WHERE c.parent_id = :pid AND c.is_active = true
            """
        ),
        {"pid": root_id},
    ).scalar_one()
    if int(nonempty or 0) != STATIONERY_V2_EXPECTED_L2_COUNT:
        raise RuntimeError(
            f"Stationery V2 Package A STOP: expected "
            f"{STATIONERY_V2_EXPECTED_L2_COUNT} non-empty Create cores, got {nonempty}"
        )

    root_cores = bind.execute(
        text(
            "SELECT count(*) FROM category_core_fields WHERE category_id = :cid"
        ),
        {"cid": root_id},
    ).scalar_one()
    if int(root_cores or 0) != 0:
        raise RuntimeError("Stationery root must remain picker-only (0 cores)")


def downgrade() -> None:
    pass
