"""Sport / Recreation / Hobbies V2 Package A — Create SoT cores.

Revision ID: c4d5e6f7a8b9sphpa
Revises: b3c4d5e6f7a8sphtax
Create Date: 2026-11-13

- Seed Create cores on all 13 active Sport L2
- Root remains picker-only (0 cores / 0 filters)
- Legacy triad + national craft stay inactive / empty
- Semantic Condition positive allowlist (85 YES / 11 NO)
- Does NOT seed Package B Search filters
"""
from __future__ import annotations

import json

from alembic import op
from sqlalchemy import text

revision = "c4d5e6f7a8b9sphpa"
down_revision = "b3c4d5e6f7a8sphtax"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from app.seeds.sport_v2 import (
        SPORT_ROOT_LABEL,
        SPORT_ROOT_SLUG,
        SPORT_V2_CANONICAL_LEAVES,
        SPORT_V2_CANONICAL_SLUGS,
        SPORT_V2_ENTITY_TYPE,
        SPORT_V2_EXPECTED_L2_COUNT,
        SPORT_V2_RETIRED_SLUGS,
        build_sport_v2_core_fields,
        sport_v2_assert_package_a_contracts,
        sport_v2_condition_matrix,
        sport_v2_kind_count,
    )

    sport_v2_assert_package_a_contracts()
    if sport_v2_kind_count() != 96:
        raise RuntimeError("Sport Package A STOP: kind count != 96")
    if sport_v2_condition_matrix() != {"YES": 85, "NO": 11}:
        raise RuntimeError("Sport Package A STOP: Condition matrix != 85/11")

    bind = op.get_bind()

    root = bind.execute(
        text("SELECT id FROM categories WHERE slug = :slug"),
        {"slug": SPORT_ROOT_SLUG},
    ).fetchone()
    if root is None:
        raise RuntimeError("sports-hobby root missing")
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
            f"Sport Package A STOP: unexpected listings ({total})"
        )

    entity_type = (
        SPORT_V2_ENTITY_TYPE.value
        if hasattr(SPORT_V2_ENTITY_TYPE, "value")
        else str(SPORT_V2_ENTITY_TYPE)
    )

    bind.execute(
        text(
            "UPDATE categories SET is_active = true, parent_id = NULL, "
            "name = :name, updated_at = now() WHERE id = :id"
        ),
        {"name": SPORT_ROOT_LABEL, "id": root_id},
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
    for label, slug, sort_order in SPORT_V2_CANONICAL_LEAVES:
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

    for slug in sorted(SPORT_V2_RETIRED_SLUGS):
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
        if slug in SPORT_V2_CANONICAL_SLUGS:
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

    for slug, fields in build_sport_v2_core_fields().items():
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
    if int(active or 0) != SPORT_V2_EXPECTED_L2_COUNT:
        raise RuntimeError(
            f"Sport Package A STOP: expected {SPORT_V2_EXPECTED_L2_COUNT} "
            f"active L2, got {active}"
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
    if int(nonempty or 0) != SPORT_V2_EXPECTED_L2_COUNT:
        raise RuntimeError(
            f"Sport Package A STOP: expected {SPORT_V2_EXPECTED_L2_COUNT} "
            f"L2 with cores, got {nonempty}"
        )

    root_cores = bind.execute(
        text(
            "SELECT count(*) FROM category_core_fields WHERE category_id = :cid"
        ),
        {"cid": root_id},
    ).scalar_one()
    if int(root_cores or 0) != 0:
        raise RuntimeError("Sport root must remain picker-only")

    forbidden_hits = bind.execute(
        text(
            """
            SELECT cc.field_key, count(*)
            FROM category_core_fields cc
            JOIN categories c ON c.id = cc.category_id
            WHERE c.parent_id = :pid
              AND cc.field_key IN (
                'size','brand','model','material','color','weight','length',
                'price_basis','gender','age','level','frame_size'
              )
            GROUP BY cc.field_key
            """
        ),
        {"pid": root_id},
    ).fetchall()
    if forbidden_hits:
        raise RuntimeError(
            f"Sport Package A STOP: forbidden cores present: {forbidden_hits}"
        )


def downgrade() -> None:
    # Package A cores are not auto-removed on downgrade.
    pass
