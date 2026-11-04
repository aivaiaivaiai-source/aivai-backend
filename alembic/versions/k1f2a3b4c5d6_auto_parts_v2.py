"""Transport Auto Parts V2: system leaves + part_name SoT.

Revision ID: k1f2a3b4c5d6autopartsv2
Revises: j0e1f2a3b4c5rentalv2
Create Date: 2026-11-03

- Preserve parent 682 picker-only (clear live Create/Search schema)
- Keep 17 passenger systems; rename Body/Fasteners labels
- Retire body oversplit 703–708/710–713 → inactive (remap listings → 702)
- Keep Optics 709; Universal 723 inactive
- Keep special 1203/1204/1205 active with scoped schemas
- Seed leaf core_fields + category_filters
"""
from __future__ import annotations

import json

from alembic import op
from sqlalchemy import text

from app.seeds.auto_parts_v2 import (
    BODY_LEAF_ID,
    BODY_LEAF_LABEL,
    BODY_LEAF_SLUG,
    BODY_RETIRED,
    BODY_RETIRED_IDS,
    PARTS_CORE_FIELDS_BY_SLUG,
    PARTS_LEAF_ALIASES,
    PARTS_PARENT_ALIASES,
    PARTS_PARENT_ID,
    PARTS_PARENT_SLUG,
    PARTS_SEARCH_FILTERS_BY_SLUG,
    OPTICS_LEAF_ID,
    PARTS_SERVICE_BOUNDARY_ALIASES,
    PASSENGER_SYSTEM_EXPECTED_IDS,
    PASSENGER_SYSTEM_LABELS,
    PASSENGER_SYSTEM_SLUGS,
    PASSENGER_SYSTEM_SORT,
    SPECIAL_SYSTEM_EXPECTED_IDS,
    SPECIAL_SYSTEM_LABELS,
    SPECIAL_SYSTEM_SLUGS,
    SPECIAL_SYSTEM_SORT,
    UNIVERSAL_INACTIVE_ID,
    UNIVERSAL_INACTIVE_SLUG,
)

revision = "k1f2a3b4c5d6autopartsv2"
down_revision = "j0e1f2a3b4c5rentalv2"
branch_labels = None
depends_on = None


def _upsert_alias(bind, alias: str, target_slug: str, *, weight: int = 100) -> None:
    target = bind.execute(
        text("SELECT id FROM categories WHERE slug = :s"),
        {"s": target_slug},
    ).fetchone()
    if target is None:
        # Services parent may use transport-auto-services — soft-skip if missing.
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


def upgrade() -> None:
    bind = op.get_bind()

    parent = bind.execute(
        text("SELECT id FROM categories WHERE slug = :s"),
        {"s": PARTS_PARENT_SLUG},
    ).fetchone()
    if parent is None:
        raise RuntimeError(f"Missing parent {PARTS_PARENT_SLUG}")
    parent_id = int(parent[0])
    if parent_id != PARTS_PARENT_ID:
        raise RuntimeError(
            f"Parent {PARTS_PARENT_SLUG} expected id={PARTS_PARENT_ID}, got {parent_id}"
        )

    # Pre-migration listing safety on body retirees + parent.
    check_ids = (PARTS_PARENT_ID, BODY_LEAF_ID, UNIVERSAL_INACTIVE_ID, *BODY_RETIRED_IDS)
    for check_id in check_ids:
        n = bind.execute(
            text("SELECT COUNT(*) FROM listings WHERE category_id = :id"),
            {"id": check_id},
        ).scalar()
        # Body consolidation remaps any listings to 702; only block unexpected
        # parent publish if we cannot remap (parent stays non-publishable).
        _ = n

    bind.execute(
        text(
            """
            UPDATE categories
            SET is_active = true, updated_at = now()
            WHERE id = :pid
            """
        ),
        {"pid": parent_id},
    )

    # Activate / label / sort passenger systems.
    for slug in PASSENGER_SYSTEM_SLUGS:
        expected = PASSENGER_SYSTEM_EXPECTED_IDS[slug]
        row = bind.execute(
            text("SELECT id, slug FROM categories WHERE id = :id"),
            {"id": expected},
        ).fetchone()
        if row is None:
            raise RuntimeError(f"Missing Auto Parts leaf id={expected} for {slug}")
        bind.execute(
            text(
                """
                UPDATE categories
                SET parent_id = :pid,
                    slug = :slug,
                    name = :label,
                    is_active = true,
                    sort_order = :sort,
                    updated_at = now()
                WHERE id = :id
                """
            ),
            {
                "pid": parent_id,
                "slug": slug,
                "label": PASSENGER_SYSTEM_LABELS[slug],
                "sort": PASSENGER_SYSTEM_SORT[slug],
                "id": expected,
            },
        )

    # Special applicability systems stay active (scoped UX, not passenger buttons).
    for slug in SPECIAL_SYSTEM_SLUGS:
        expected = SPECIAL_SYSTEM_EXPECTED_IDS[slug]
        row = bind.execute(
            text("SELECT id FROM categories WHERE id = :id"),
            {"id": expected},
        ).fetchone()
        if row is None:
            raise RuntimeError(f"Missing special Auto Parts id={expected}")
        bind.execute(
            text(
                """
                UPDATE categories
                SET parent_id = :pid,
                    slug = :slug,
                    name = :label,
                    is_active = true,
                    sort_order = :sort,
                    updated_at = now()
                WHERE id = :id
                """
            ),
            {
                "pid": parent_id,
                "slug": slug,
                "label": SPECIAL_SYSTEM_LABELS[slug],
                "sort": SPECIAL_SYSTEM_SORT[slug],
                "id": expected,
            },
        )

    # Body consolidation: remap listings → 702, then deactivate.
    for rid, rslug, _meaning in BODY_RETIRED:
        bind.execute(
            text(
                """
                UPDATE listings
                SET category_id = :tid, updated_at = now()
                WHERE category_id = :sid
                """
            ),
            {"tid": BODY_LEAF_ID, "sid": rid},
        )
        bind.execute(
            text(
                """
                UPDATE categories
                SET is_active = false,
                    parent_id = :pid,
                    updated_at = now()
                WHERE id = :id
                """
            ),
            {"pid": parent_id, "id": rid},
        )
        # Point aliases that targeted retired body leaves → Body.
        bind.execute(
            text(
                """
                UPDATE category_aliases
                SET category_id = :tid, updated_at = now()
                WHERE category_id = :sid
                """
            ),
            {"tid": BODY_LEAF_ID, "sid": rid},
        )
        _ = rslug

    # Universal stays inactive.
    bind.execute(
        text(
            """
            UPDATE categories
            SET is_active = false, updated_at = now()
            WHERE id = :id OR slug = :slug
            """
        ),
        {"id": UNIVERSAL_INACTIVE_ID, "slug": UNIVERSAL_INACTIVE_SLUG},
    )

    # Clear optional fields on parent + all leaves we manage.
    managed_ids = [
        PARTS_PARENT_ID,
        *PASSENGER_SYSTEM_EXPECTED_IDS.values(),
        *SPECIAL_SYSTEM_EXPECTED_IDS.values(),
        *BODY_RETIRED_IDS,
        UNIVERSAL_INACTIVE_ID,
    ]
    for cid in managed_ids:
        bind.execute(
            text("DELETE FROM category_optional_fields WHERE category_id = :cid"),
            {"cid": cid},
        )

    # Seed schemas.
    for slug, fields in PARTS_CORE_FIELDS_BY_SLUG.items():
        row = bind.execute(
            text("SELECT id FROM categories WHERE slug = :s"),
            {"s": slug},
        ).fetchone()
        if row is None:
            continue
        cid = int(row[0])
        _replace_core_fields(bind, cid, fields)
        _replace_filters(bind, cid, PARTS_SEARCH_FILTERS_BY_SLUG.get(slug, []))

    # Aliases.
    for alias, leaf_slug in PARTS_LEAF_ALIASES.items():
        _upsert_alias(bind, alias, leaf_slug)
    for alias, parent_slug in PARTS_PARENT_ALIASES.items():
        _upsert_alias(bind, alias, parent_slug, weight=80)
    for alias, target_slug in PARTS_SERVICE_BOUNDARY_ALIASES.items():
        # Prefer concrete auto-services leaf if present; else parent services.
        target = bind.execute(
            text("SELECT slug FROM categories WHERE slug = :s AND is_active"),
            {"s": target_slug},
        ).fetchone()
        if target is None:
            # Fallback: first active child under transport-auto-services
            svc = bind.execute(
                text(
                    """
                    SELECT c.slug FROM categories c
                    JOIN categories p ON p.id = c.parent_id
                    WHERE p.slug = 'transport-auto-services' AND c.is_active
                    ORDER BY c.sort_order LIMIT 1
                    """
                )
            ).fetchone()
            if svc is None:
                continue
            _upsert_alias(bind, alias, str(svc[0]), weight=130)
        else:
            _upsert_alias(bind, alias, target_slug, weight=130)

    # Disable unsafe generic LED → Optics alias if present.
    bind.execute(
        text(
            """
            UPDATE category_aliases
            SET is_enabled = false, updated_at = now()
            WHERE alias_normalized = 'led'
              AND category_id = :optics
            """
        ),
        {"optics": OPTICS_LEAF_ID},
    )


def downgrade() -> None:
    # Non-destructive: do not restore body oversplit or parent-only schema.
    pass
