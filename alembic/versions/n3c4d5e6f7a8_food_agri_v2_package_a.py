"""Food/Agri V2 Package A — Create SoT for 23 edible L2.

Revision ID: n3c4d5e6f7a8foodpacka
Revises: m2b3c4d5e6f7foodtax
Create Date: 2026-11-11

- Keep root food-agri picker-only
- Ensure 23 canonical active L2
- Seed Create cores: food_kind, seller_type (Food override), price,
  price_basis (optional), negotiable, contact_methods
- No Search filters (Package B)
- STOP if unexpected Food listings appear
"""
from __future__ import annotations

import json

from alembic import op
from sqlalchemy import text

revision = "n3c4d5e6f7a8foodpacka"
down_revision = "m2b3c4d5e6f7foodtax"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from app.seeds.food_agri_v2 import (
        FOOD_AGRI_ROOT_LABEL,
        FOOD_AGRI_ROOT_SLUG,
        FOOD_AGRI_V2_CANONICAL_LEAVES,
        FOOD_AGRI_V2_CANONICAL_SLUGS,
        FOOD_AGRI_V2_EXPECTED_L2_COUNT,
        FOOD_AGRI_V2_RETIRED_SLUGS,
        build_food_agri_v2_core_fields,
    )

    bind = op.get_bind()

    root = bind.execute(
        text("SELECT id FROM categories WHERE slug = :slug"),
        {"slug": FOOD_AGRI_ROOT_SLUG},
    ).fetchone()
    if root is None:
        raise RuntimeError("food-agri root missing")
    root_id = int(root[0])

    total = bind.execute(
        text(
            """
            WITH RECURSIVE t AS (
              SELECT id FROM categories WHERE id = :rid
              UNION ALL
              SELECT c.id FROM categories c JOIN t ON c.parent_id = t.id
            )
            SELECT count(*) FROM listings l JOIN t ON l.category_id = t.id
            """
        ),
        {"rid": root_id},
    ).scalar_one()
    if int(total or 0) > 0:
        raise RuntimeError(
            f"Food/Agri V2 Package A STOP: unexpected listings ({total})"
        )

    bind.execute(
        text(
            """
            UPDATE categories
            SET name = :name, is_active = true, parent_id = NULL, updated_at = now()
            WHERE id = :id
            """
        ),
        {"name": FOOD_AGRI_ROOT_LABEL, "id": root_id},
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

    slug_to_id: dict[str, int] = {FOOD_AGRI_ROOT_SLUG: root_id}

    for label, slug, sort_order in FOOD_AGRI_V2_CANONICAL_LEAVES:
        row = bind.execute(
            text("SELECT id FROM categories WHERE slug = :slug"),
            {"slug": slug},
        ).fetchone()
        if row is None:
            raise RuntimeError(
                f"Food/Agri V2 Package A STOP: missing canonical leaf {slug}"
            )
        cid = int(row[0])
        slug_to_id[slug] = cid
        bind.execute(
            text(
                """
                UPDATE categories
                SET parent_id = :pid,
                    name = :name,
                    is_active = true,
                    sort_order = :sort,
                    entity_type = 'food',
                    requires_city = true,
                    updated_at = now()
                WHERE id = :id
                """
            ),
            {"pid": root_id, "name": label, "sort": sort_order, "id": cid},
        )

    for slug in sorted(FOOD_AGRI_V2_RETIRED_SLUGS):
        row = bind.execute(
            text("SELECT id FROM categories WHERE slug = :slug"),
            {"slug": slug},
        ).fetchone()
        if row is None:
            continue
        cid = int(row[0])
        slug_to_id[slug] = cid
        bind.execute(
            text(
                """
                UPDATE categories
                SET is_active = false, updated_at = now()
                WHERE id = :id
                """
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
        if slug in FOOD_AGRI_V2_CANONICAL_SLUGS:
            continue
        bind.execute(
            text(
                """
                UPDATE categories
                SET is_active = false, updated_at = now()
                WHERE id = :id
                """
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

    core_by_slug = build_food_agri_v2_core_fields()
    for slug, fields in core_by_slug.items():
        cid = slug_to_id[slug]
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

    active = bind.execute(
        text(
            """
            SELECT count(*) FROM categories
            WHERE parent_id = :pid AND is_active = true
            """
        ),
        {"pid": root_id},
    ).scalar_one()
    if int(active or 0) != FOOD_AGRI_V2_EXPECTED_L2_COUNT:
        raise RuntimeError(
            f"Food/Agri V2 Package A STOP: expected "
            f"{FOOD_AGRI_V2_EXPECTED_L2_COUNT} active L2, got {active}"
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
    if int(nonempty or 0) != FOOD_AGRI_V2_EXPECTED_L2_COUNT:
        raise RuntimeError(
            "Food/Agri V2 Package A STOP: expected "
            f"{FOOD_AGRI_V2_EXPECTED_L2_COUNT} non-empty Create schemas, "
            f"got {nonempty}"
        )


def downgrade() -> None:
    pass
