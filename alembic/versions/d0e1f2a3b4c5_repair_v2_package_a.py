"""Repair V2 Package A — canonical goods taxonomy + Create SoT.

Revision ID: d0e1f2a3b4c5repairv2a
Revises: c9d0e1f2a3b4svcpkgb
Create Date: 2026-11-07

- Keep root repair-construction (picker-only)
- Ensure 28 canonical active goods L2 + approved labels
- Retire legacy repair-building / construction-work / repair-tools
- Seed shared Create core fields (repair_kind/seller/price/…)
- Align aliases: goods words → goods; work phrases → Services
- STOP if unexpected listings appear on Repair subtree
"""
from __future__ import annotations

import json

from alembic import op
from sqlalchemy import text

revision = "d0e1f2a3b4c5repairv2a"
down_revision = "c9d0e1f2a3b4svcpkgb"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from app.seeds.repair_v2 import (
        REPAIR_ROOT_SLUG,
        REPAIR_V2_ALIAS_REMAP,
        REPAIR_V2_CANONICAL_LEAVES,
        REPAIR_V2_CANONICAL_SLUGS,
        REPAIR_V2_RETIRED_SLUGS,
        build_repair_v2_core_fields,
    )

    bind = op.get_bind()

    root = bind.execute(
        text("SELECT id FROM categories WHERE slug = :slug"),
        {"slug": REPAIR_ROOT_SLUG},
    ).fetchone()
    if root is None:
        raise RuntimeError("repair-construction root missing")
    root_id = int(root[0])

    # Safety: any listings in Repair subtree → STOP.
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
            f"Repair V2 Package A STOP: unexpected listings in Repair subtree ({total})"
        )

    bind.execute(
        text(
            """
            UPDATE categories
            SET name = 'Ремонт и строительство', is_active = true, updated_at = now()
            WHERE id = :id
            """
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

    slug_to_id: dict[str, int] = {REPAIR_ROOT_SLUG: root_id}

    for slug, label, sort_order in REPAIR_V2_CANONICAL_LEAVES:
        row = bind.execute(
            text("SELECT id FROM categories WHERE slug = :slug"),
            {"slug": slug},
        ).fetchone()
        if row is None:
            raise RuntimeError(f"Repair V2 Package A STOP: missing canonical leaf {slug}")
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
                    entity_type = 'construction',
                    requires_city = true,
                    updated_at = now()
                WHERE id = :id
                """
            ),
            {"pid": root_id, "name": label, "sort": sort_order, "id": cid},
        )

    for slug in sorted(REPAIR_V2_RETIRED_SLUGS):
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

    # Deactivate any unexpected active children.
    children = bind.execute(
        text("SELECT id, slug FROM categories WHERE parent_id = :pid"),
        {"pid": root_id},
    ).fetchall()
    for cid, slug in children:
        if slug in REPAIR_V2_CANONICAL_SLUGS:
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

    core_by_slug = build_repair_v2_core_fields()
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
                    if options is not None
                    else None,
                },
            )

    # Resolve Services construction leaf for work aliases.
    svc = bind.execute(
        text(
            "SELECT id FROM categories WHERE slug = 'services-stroitelnye-i-remontnye-uslugi'"
        )
    ).fetchone()
    if svc is not None:
        slug_to_id["services-stroitelnye-i-remontnye-uslugi"] = int(svc[0])

    for alias, target in REPAIR_V2_ALIAS_REMAP.items():
        target_id = slug_to_id.get(target)
        if target_id is None:
            continue
        existing = bind.execute(
            text(
                """
                SELECT id FROM category_aliases
                WHERE alias_normalized = :alias AND locale = 'ru'
                """
            ),
            {"alias": alias},
        ).fetchone()
        if existing is None:
            bind.execute(
                text(
                    """
                    INSERT INTO category_aliases (
                      category_id, alias, alias_normalized, alias_compact,
                      locale, weight, is_enabled, created_at, updated_at
                    ) VALUES (
                      :cid, :alias, :alias, :compact,
                      'ru', 120, true, now(), now()
                    )
                    """
                ),
                {
                    "cid": target_id,
                    "alias": alias,
                    "compact": alias.replace(" ", ""),
                },
            )
        else:
            bind.execute(
                text(
                    """
                    UPDATE category_aliases
                    SET category_id = :cid,
                        alias = :alias,
                        is_enabled = true,
                        weight = 120,
                        updated_at = now()
                    WHERE id = :id
                    """
                ),
                {"cid": target_id, "alias": alias, "id": int(existing[0])},
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
    if int(active or 0) != 28:
        raise RuntimeError(
            f"Repair V2 Package A STOP: expected 28 active L2, got {active}"
        )


def downgrade() -> None:
    # Irreversible Package A overlay; restore from backup if needed.
    pass
