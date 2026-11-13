"""Beauty & Personal Care V2 Package A — Create SoT cores.

Revision ID: f7a8b9c0d1e2beautypa
Revises: e6f7a8b9c0d1beauty
Create Date: 2026-11-13

- Seed Create cores on all 16 active Beauty L2
- Root remains picker-only (0 cores / 0 filters)
- Legacy beauty-cosmetics / beauty-hair stay inactive / empty
- Semantic Condition positive allowlist (18 YES / 81 NO)
- No package_state / brand / model / SKU fields
- Does NOT seed Package B Search filters
"""
from __future__ import annotations

import json

from alembic import op
from sqlalchemy import text

revision = "f7a8b9c0d1e2beautypa"
down_revision = "e6f7a8b9c0d1beauty"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from app.seeds.beauty_v2 import (
        BEAUTY_ROOT_LABEL,
        BEAUTY_ROOT_SLUG,
        BEAUTY_V2_CANONICAL_LEAVES,
        BEAUTY_V2_CANONICAL_SLUGS,
        BEAUTY_V2_RETIRED_SLUGS,
        build_beauty_v2_core_fields,
        beauty_v2_assert_package_a_contracts,
        beauty_v2_condition_matrix,
        beauty_v2_kind_count,
    )

    beauty_v2_assert_package_a_contracts()
    if beauty_v2_kind_count() != 99:
        raise RuntimeError("Beauty Package A STOP: kind count != 99")
    if beauty_v2_condition_matrix() != {"YES": 18, "NO": 81}:
        raise RuntimeError("Beauty Package A STOP: Condition matrix != 18/81")

    bind = op.get_bind()

    root = bind.execute(
        text("SELECT id FROM categories WHERE slug = :slug"),
        {"slug": BEAUTY_ROOT_SLUG},
    ).fetchone()
    if root is None:
        raise RuntimeError("beauty root missing")
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
            f"Beauty Package A STOP: unexpected listings ({total})"
        )

    bind.execute(
        text(
            "UPDATE categories SET is_active = true, parent_id = NULL, "
            "name = :name, updated_at = now() WHERE id = :id"
        ),
        {"name": BEAUTY_ROOT_LABEL, "id": root_id},
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
    for label, slug, sort_order in BEAUTY_V2_CANONICAL_LEAVES:
        row = bind.execute(
            text("SELECT id FROM categories WHERE slug = :slug"),
            {"slug": slug},
        ).fetchone()
        if row is None:
            raise RuntimeError(f"Beauty Package A STOP: missing leaf {slug}")
        bind.execute(
            text(
                """
                UPDATE categories
                SET parent_id = :pid, name = :name, is_active = true,
                    sort_order = :sort, requires_city = true, updated_at = now()
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

    for slug in sorted(BEAUTY_V2_RETIRED_SLUGS):
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
        if slug in BEAUTY_V2_CANONICAL_SLUGS:
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
            ftype_val = ftype.value if hasattr(ftype, "value") else str(ftype)
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
                    "ftype": ftype_val,
                    "req": bool(required),
                    "sort": int(sort),
                    "hint": hint,
                    "options": json.dumps(options, ensure_ascii=False)
                    if options is not None
                    else None,
                },
            )

    cores = build_beauty_v2_core_fields()
    if set(cores.keys()) != BEAUTY_V2_CANONICAL_SLUGS:
        raise RuntimeError("Beauty Package A STOP: cores map ≠ canonical L2")
    for slug, fields in cores.items():
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
    if int(active or 0) != 16:
        raise RuntimeError(
            f"Beauty Package A STOP: expected 16 active L2, got {active}"
        )

    nonempty = bind.execute(
        text(
            """
            SELECT count(DISTINCT c.id)
            FROM categories c
            JOIN category_core_fields cf ON cf.category_id = c.id
            WHERE c.parent_id = :pid AND c.is_active = true
            """
        ),
        {"pid": root_id},
    ).scalar_one()
    if int(nonempty or 0) != 16:
        raise RuntimeError(
            f"Beauty Package A STOP: expected 16 L2 with cores, got {nonempty}"
        )


def downgrade() -> None:
    # Package A cores are not auto-reverted.
    pass
