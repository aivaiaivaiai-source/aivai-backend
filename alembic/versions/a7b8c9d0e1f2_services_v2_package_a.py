"""Services V2 Package A — canonical taxonomy + Create SoT.

Revision ID: a7b8c9d0e1f2servicesv2a
Revises: z6a7b8c9d0e1jobslegacy
Create Date: 2026-11-07

- Keep root services (picker-only)
- Ensure 31 canonical active L2 leaves + labels
- Add services-rieltorskie-uslugi
- Retire legacy 7 + merged/removed skeleton leaves
- Seed shared Create core fields (service_kind/executor/price/…)
- Preserve draft on services-transport (no remap)
- Stop if unexpected active Services listings appear on retire candidates
"""
from __future__ import annotations

import json

from alembic import op
from sqlalchemy import text

revision = "a7b8c9d0e1f2servicesv2a"
down_revision = "z6a7b8c9d0e1jobslegacy"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from app.seeds.services_v2 import (
        SERVICES_ROOT_SLUG,
        SERVICES_V2_ALIAS_REMAP,
        SERVICES_V2_CANONICAL_LEAVES,
        SERVICES_V2_CANONICAL_SLUGS,
        SERVICES_V2_MERGE_TARGETS,
        SERVICES_V2_RETIRED_SLUGS,
        build_services_v2_core_fields,
    )

    bind = op.get_bind()

    root = bind.execute(
        text("SELECT id FROM categories WHERE slug = :slug"),
        {"slug": SERVICES_ROOT_SLUG},
    ).fetchone()
    if root is None:
        raise RuntimeError("services root missing")
    root_id = int(root[0])
    bind.execute(
        text(
            """
            UPDATE categories
            SET name = 'Услуги', is_active = true, updated_at = now()
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

    # Safety: refuse unexpected active listings on nodes we retire/merge.
    for slug in sorted(SERVICES_V2_RETIRED_SLUGS | set(SERVICES_V2_MERGE_TARGETS)):
        row = bind.execute(
            text("SELECT id FROM categories WHERE slug = :slug"),
            {"slug": slug},
        ).fetchone()
        if row is None:
            continue
        cid = int(row[0])
        active = bind.execute(
            text(
                """
                SELECT count(*) FROM listings
                WHERE category_id = :cid AND status = 'active'
                """
            ),
            {"cid": cid},
        ).scalar_one()
        if int(active or 0) > 0:
            raise RuntimeError(
                f"Services V2 Package A STOP: active listings on {slug}"
            )

    # Upsert canonical leaves.
    for slug, label, sort_order in SERVICES_V2_CANONICAL_LEAVES:
        row = bind.execute(
            text("SELECT id FROM categories WHERE slug = :slug"),
            {"slug": slug},
        ).fetchone()
        if row is None:
            bind.execute(
                text(
                    """
                    INSERT INTO categories (
                        parent_id, slug, name, entity_type, is_active,
                        sort_order, requires_city, created_at, updated_at
                    ) VALUES (
                        :parent_id, :slug, :name, 'service', true,
                        :sort_order, true, now(), now()
                    )
                    """
                ),
                {
                    "parent_id": root_id,
                    "slug": slug,
                    "name": label,
                    "sort_order": sort_order,
                },
            )
        else:
            bind.execute(
                text(
                    """
                    UPDATE categories
                    SET parent_id = :parent_id,
                        name = :name,
                        entity_type = 'service',
                        is_active = true,
                        sort_order = :sort_order,
                        requires_city = true,
                        updated_at = now()
                    WHERE id = :id
                    """
                ),
                {
                    "parent_id": root_id,
                    "name": label,
                    "sort_order": sort_order,
                    "id": int(row[0]),
                },
            )

    # Retire non-canonical Services children.
    children = bind.execute(
        text("SELECT id, slug FROM categories WHERE parent_id = :pid"),
        {"pid": root_id},
    ).fetchall()
    for cid, slug in children:
        if slug in SERVICES_V2_CANONICAL_SLUGS:
            continue
        listing_count = bind.execute(
            text("SELECT count(*) FROM listings WHERE category_id = :cid"),
            {"cid": int(cid)},
        ).scalar_one()
        bind.execute(
            text(
                """
                UPDATE categories
                SET is_active = false, updated_at = now()
                WHERE id = :cid
                """
            ),
            {"cid": int(cid)},
        )
        if int(listing_count or 0) == 0:
            for table in (
                "category_core_fields",
                "category_optional_fields",
                "category_filters",
            ):
                bind.execute(
                    text(f"DELETE FROM {table} WHERE category_id = :cid"),
                    {"cid": int(cid)},
                )

    # Seed Create SoT on canonical leaves.
    core_by_slug = build_services_v2_core_fields()
    for slug, fields in core_by_slug.items():
        row = bind.execute(
            text("SELECT id FROM categories WHERE slug = :slug"),
            {"slug": slug},
        ).fetchone()
        if row is None:
            raise RuntimeError(f"canonical leaf missing after upsert: {slug}")
        cid = int(row[0])
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

    # Remap useful aliases onto canonical leaves.
    for alias, target_slug in SERVICES_V2_ALIAS_REMAP.items():
        target = bind.execute(
            text("SELECT id FROM categories WHERE slug = :slug"),
            {"slug": target_slug},
        ).fetchone()
        if target is None:
            continue
        tid = int(target[0])
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
                    "cid": tid,
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
                {"cid": tid, "alias": alias, "id": int(existing[0])},
            )


def downgrade() -> None:
    # Non-destructive: do not resurrect retired dual-tree automatically.
    pass
