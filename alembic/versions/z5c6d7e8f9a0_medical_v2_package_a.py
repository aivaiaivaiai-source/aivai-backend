"""Medical Goods V2 Package A — Create SoT cores.

Revision ID: z5c6d7e8f9a0medpa
Revises: y4b5c6d7e8f9medtax
Create Date: 2026-11-12

- Seed Create cores on all 15 active Medical L2
- Root remains picker-only (0 cores / 0 filters)
- Retired legacy dual tree + БАДы stay empty / inactive
- Listing 3154 (LEGACY_INCOMPLETE) may exist — schema metadata only;
  no EAV/listing mutation / no backfill
- Does NOT seed Package B Search filters
"""
from __future__ import annotations

import json

from alembic import op
from sqlalchemy import text

revision = "z5c6d7e8f9a0medpa"
down_revision = "y4b5c6d7e8f9medtax"
branch_labels = None
depends_on = None

LEGACY_INCOMPLETE_LISTING_ID = 3154


def upgrade() -> None:
    from app.seeds.medical_v2 import (
        MEDICAL_ROOT_LABEL,
        MEDICAL_ROOT_SLUG,
        MEDICAL_V2_CANONICAL_LEAVES,
        MEDICAL_V2_CANONICAL_SLUGS,
        MEDICAL_V2_ENTITY_TYPE,
        MEDICAL_V2_EXPECTED_L2_COUNT,
        MEDICAL_V2_RETIRED_SLUGS,
        build_medical_v2_core_fields,
        medical_v2_assert_package_a_contracts,
    )

    medical_v2_assert_package_a_contracts()
    bind = op.get_bind()

    root = bind.execute(
        text("SELECT id FROM categories WHERE slug = :slug"),
        {"slug": MEDICAL_ROOT_SLUG},
    ).fetchone()
    if root is None:
        raise RuntimeError("medical root missing")
    root_id = int(root[0])

    # Fingerprint legacy incomplete listing before schema seed (must not mutate).
    legacy_before = None
    legacy_eav_before: list[tuple] = []
    legacy_row = bind.execute(
        text(
            """
            SELECT id, title, status, price::text, currency, owner_id, category_id,
                   description, updated_at::text
            FROM listings WHERE id = :lid
            """
        ),
        {"lid": LEGACY_INCOMPLETE_LISTING_ID},
    ).fetchone()
    if legacy_row is not None:
        legacy_before = tuple(legacy_row)
        legacy_eav_before = bind.execute(
            text(
                """
                SELECT field_key, value_text, value_int,
                       value_decimal::text, value_bool
                FROM listing_field_values
                WHERE listing_id = :lid
                ORDER BY field_key
                """
            ),
            {"lid": LEGACY_INCOMPLETE_LISTING_ID},
        ).fetchall()

    entity_type = (
        MEDICAL_V2_ENTITY_TYPE.value
        if hasattr(MEDICAL_V2_ENTITY_TYPE, "value")
        else str(MEDICAL_V2_ENTITY_TYPE)
    )

    bind.execute(
        text(
            "UPDATE categories SET is_active = true, parent_id = NULL, "
            "name = :name, updated_at = now() WHERE id = :id"
        ),
        {"name": MEDICAL_ROOT_LABEL, "id": root_id},
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
    for label, slug, sort_order in MEDICAL_V2_CANONICAL_LEAVES:
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
                      (:pid, :slug, :name, :etype, true, :sort, true, now(), now())
                    """
                ),
                {
                    "pid": root_id,
                    "slug": slug,
                    "name": label,
                    "etype": entity_type,
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
                        sort_order = :sort, entity_type = :etype,
                        requires_city = true, updated_at = now()
                    WHERE id = :id
                    """
                ),
                {
                    "pid": root_id,
                    "name": label,
                    "sort": sort_order,
                    "etype": entity_type,
                    "id": int(row[0]),
                },
            )
        slug_to_id[slug] = int(row[0])

    for slug in sorted(MEDICAL_V2_RETIRED_SLUGS):
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
        if slug in MEDICAL_V2_CANONICAL_SLUGS:
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

    for slug, fields in build_medical_v2_core_fields().items():
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
    if int(active or 0) != MEDICAL_V2_EXPECTED_L2_COUNT:
        raise RuntimeError(
            f"Medical Package A STOP: expected "
            f"{MEDICAL_V2_EXPECTED_L2_COUNT} active L2, got {active}"
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
    if int(nonempty or 0) != MEDICAL_V2_EXPECTED_L2_COUNT:
        raise RuntimeError(
            f"Medical Package A STOP: expected "
            f"{MEDICAL_V2_EXPECTED_L2_COUNT} non-empty Create cores, "
            f"got {nonempty}"
        )

    root_cores = bind.execute(
        text(
            "SELECT count(*) FROM category_core_fields WHERE category_id = :cid"
        ),
        {"cid": root_id},
    ).scalar_one()
    if int(root_cores or 0) != 0:
        raise RuntimeError("Medical root must remain picker-only (0 cores)")

    # Legacy incomplete listing must remain byte-identical (no backfill).
    if legacy_before is not None:
        legacy_after = bind.execute(
            text(
                """
                SELECT id, title, status, price::text, currency, owner_id, category_id,
                       description, updated_at::text
                FROM listings WHERE id = :lid
                """
            ),
            {"lid": LEGACY_INCOMPLETE_LISTING_ID},
        ).fetchone()
        if tuple(legacy_after) != legacy_before:
            raise RuntimeError(
                "LISTING 3154 MODIFIED during Medical Package A migration"
            )
        legacy_eav_after = bind.execute(
            text(
                """
                SELECT field_key, value_text, value_int,
                       value_decimal::text, value_bool
                FROM listing_field_values
                WHERE listing_id = :lid
                ORDER BY field_key
                """
            ),
            {"lid": LEGACY_INCOMPLETE_LISTING_ID},
        ).fetchall()
        if [tuple(r) for r in legacy_eav_after] != [
            tuple(r) for r in legacy_eav_before
        ]:
            raise RuntimeError(
                "LISTING 3154 EAV mutated/backfilled during Medical Package A"
            )


def downgrade() -> None:
    # Package A cores are not auto-stripped on downgrade.
    pass
