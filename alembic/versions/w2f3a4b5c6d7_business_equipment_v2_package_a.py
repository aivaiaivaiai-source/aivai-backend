"""Business Equipment V2 Package A — Create SoT cores.

Revision ID: w2f3a4b5c6d7bizpa
Revises: v1e2f3a4b5c6biztax
Create Date: 2026-11-12

- Seed Create cores on all 20 active Business Equipment L2
- Root remains picker-only (0 cores / 0 filters)
- Retired legacy triad stay empty / inactive
- Listings may exist (e.g. 2911) — schema metadata only; no EAV/listing mutation
- Does NOT seed Package B Search filters
"""
from __future__ import annotations

import json

from alembic import op
from sqlalchemy import text

revision = "w2f3a4b5c6d7bizpa"
down_revision = "v1e2f3a4b5c6biztax"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from app.seeds.business_equipment_v2 import (
        BUSINESS_EQUIPMENT_ROOT_SLUG,
        BUSINESS_EQUIPMENT_V2_CANONICAL_LEAVES,
        BUSINESS_EQUIPMENT_V2_CANONICAL_SLUGS,
        BUSINESS_EQUIPMENT_V2_ENTITY_TYPE,
        BUSINESS_EQUIPMENT_V2_EXPECTED_L2_COUNT,
        BUSINESS_EQUIPMENT_V2_RETIRED_SLUGS,
        build_business_equipment_v2_core_fields,
        business_equipment_v2_assert_package_a_contracts,
    )

    business_equipment_v2_assert_package_a_contracts()
    bind = op.get_bind()

    root = bind.execute(
        text("SELECT id FROM categories WHERE slug = :slug"),
        {"slug": BUSINESS_EQUIPMENT_ROOT_SLUG},
    ).fetchone()
    if root is None:
        raise RuntimeError("business-equipment root missing")
    root_id = int(root[0])

    # Data safety: listings may exist (forensic 2911). Do NOT delete/mutate EAV.
    listing_n = bind.execute(
        text(
            """
            SELECT count(*) FROM listings l
            JOIN categories c ON c.id = l.category_id
            WHERE c.id = :root OR c.parent_id = :root
               OR c.slug LIKE 'business-equipment%'
            """
        ),
        {"root": root_id},
    ).scalar_one()
    # Informational only — Package A proceeds with schema metadata changes.
    _ = int(listing_n or 0)

    entity_type = (
        BUSINESS_EQUIPMENT_V2_ENTITY_TYPE.value
        if hasattr(BUSINESS_EQUIPMENT_V2_ENTITY_TYPE, "value")
        else str(BUSINESS_EQUIPMENT_V2_ENTITY_TYPE)
    )

    bind.execute(
        text(
            "UPDATE categories SET is_active = true, parent_id = NULL, "
            "name = 'Бизнес-оборудование', updated_at = now() WHERE id = :id"
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
    for label, slug, sort_order in BUSINESS_EQUIPMENT_V2_CANONICAL_LEAVES:
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

    for slug in sorted(BUSINESS_EQUIPMENT_V2_RETIRED_SLUGS):
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
        if slug in BUSINESS_EQUIPMENT_V2_CANONICAL_SLUGS:
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

    for slug, fields in build_business_equipment_v2_core_fields().items():
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
    if int(active or 0) != BUSINESS_EQUIPMENT_V2_EXPECTED_L2_COUNT:
        raise RuntimeError(
            f"Business Equipment Package A STOP: expected "
            f"{BUSINESS_EQUIPMENT_V2_EXPECTED_L2_COUNT} active L2, got {active}"
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
    if int(nonempty or 0) != BUSINESS_EQUIPMENT_V2_EXPECTED_L2_COUNT:
        raise RuntimeError(
            f"Business Equipment Package A STOP: expected "
            f"{BUSINESS_EQUIPMENT_V2_EXPECTED_L2_COUNT} non-empty Create cores, "
            f"got {nonempty}"
        )

    root_cores = bind.execute(
        text(
            "SELECT count(*) FROM category_core_fields WHERE category_id = :cid"
        ),
        {"cid": root_id},
    ).scalar_one()
    if int(root_cores or 0) != 0:
        raise RuntimeError("Business Equipment root must remain picker-only (0 cores)")

    # Forensic listing 2911 must remain untouched if present.
    forensic = bind.execute(
        text(
            """
            SELECT l.id, count(lf.id) AS eav_n
            FROM listings l
            LEFT JOIN listing_field_values lf ON lf.listing_id = l.id
            WHERE l.id = 2911
            GROUP BY l.id
            """
        )
    ).fetchone()
    if forensic is not None:
        eav_keys = bind.execute(
            text(
                """
                SELECT field_key FROM listing_field_values
                WHERE listing_id = 2911 ORDER BY field_key
                """
            )
        ).fetchall()
        keys = {r[0] for r in eav_keys}
        # Pre-Package-A incomplete: geo only — do not invent characteristics.
        if keys - {"region", "city"}:
            # Allow extra keys if historically present; never delete them here.
            pass


def downgrade() -> None:
    pass
