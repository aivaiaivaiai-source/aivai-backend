"""Transport Rental V2: 9 leaves, pricing unit, no crew.

Revision ID: j0e1f2a3b4c5rentalv2
Revises: i9d0e1f2a3b4farmv2
Create Date: 2026-11-03

- Preserve parent 695 picker-only
- Reuse 845 as combined Bus/Microbus; retire 846
- Retire Electric Rental 852
- Keep legacy 844/848/853/854 inactive
- Create Trailer / Farm / Other leaves if missing
- Seed leaf core_fields + filters; clear parent stub SoT
"""
from __future__ import annotations

import json

from alembic import op
from sqlalchemy import text

from app.seeds.transport_rental_v2 import (
    BUS_COMBINED_ID,
    BUS_COMBINED_LABEL,
    BUS_COMBINED_OLD_SLUG,
    BUS_COMBINED_SLUG,
    BUS_RETIRED_ID,
    BUS_RETIRED_SLUG,
    ELECTRIC_RENTAL_SLUG,
    FARM_RENTAL_SLUG,
    OTHER_RENTAL_SLUG,
    RENTAL_CORE_FIELDS_BY_SLUG,
    RENTAL_INACTIVE_LEGACY_SLUGS,
    RENTAL_LEAF_ALIASES,
    RENTAL_LEAF_EXPECTED_IDS,
    RENTAL_LEAF_LABELS,
    RENTAL_LEAF_SORT,
    RENTAL_LEAF_SLUGS,
    RENTAL_PARENT_ALIASES,
    RENTAL_PARENT_SLUG,
    RENTAL_REMAP_TARGETS,
    RENTAL_SEARCH_FILTERS_BY_SLUG,
    RENTAL_SERVICE_BOUNDARY_ALIASES,
    TRAILER_RENTAL_SLUG,
)

revision = "j0e1f2a3b4c5rentalv2"
down_revision = "i9d0e1f2a3b4farmv2"
branch_labels = None
depends_on = None


def _ensure_leaf(
    bind,
    *,
    parent_id: int,
    slug: str,
    label: str,
    sort: int,
    expected_id: int | None,
) -> int:
    row = bind.execute(
        text("SELECT id FROM categories WHERE slug = :s"),
        {"s": slug},
    ).fetchone()
    if row is not None:
        cid = int(row[0])
        if expected_id is not None and cid != expected_id:
            raise RuntimeError(
                f"Rental leaf {slug} must reuse id={expected_id}; got {cid}"
            )
        bind.execute(
            text(
                """
                UPDATE categories
                SET parent_id = :pid,
                    name = :label,
                    is_active = true,
                    sort_order = :sort,
                    updated_at = now()
                WHERE id = :id
                """
            ),
            {"pid": parent_id, "label": label, "sort": sort, "id": cid},
        )
        return cid

    if expected_id is not None:
        by_id = bind.execute(
            text("SELECT id, slug FROM categories WHERE id = :id"),
            {"id": expected_id},
        ).fetchone()
        if by_id is None:
            raise RuntimeError(f"Expected rental id={expected_id} missing for {slug}")
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
                "label": label,
                "sort": sort,
                "id": expected_id,
            },
        )
        return expected_id

    # Create new leaf.
    bind.execute(
        text(
            """
            INSERT INTO categories
            (name, slug, parent_id, entity_type, description, sort_order,
             is_active, requires_city, ai_dialogue_hint, created_at, updated_at)
            VALUES
            (:name, :slug, :pid, CAST('object' AS category_entity_type_enum),
             NULL, :sort, true, true, NULL, now(), now())
            """
        ),
        {"name": label, "slug": slug, "pid": parent_id, "sort": sort},
    )
    created = bind.execute(
        text("SELECT id FROM categories WHERE slug = :s"),
        {"s": slug},
    ).fetchone()
    if created is None:
        raise RuntimeError(f"Failed to create rental leaf {slug}")
    return int(created[0])


def upgrade() -> None:
    bind = op.get_bind()

    parent = bind.execute(
        text("SELECT id FROM categories WHERE slug = :s"),
        {"s": RENTAL_PARENT_SLUG},
    ).fetchone()
    if parent is None:
        raise RuntimeError(f"Missing parent {RENTAL_PARENT_SLUG}")
    parent_id = int(parent[0])

    # Reference safety: refuse destructive consolidate if live listings exist
    # on nodes we retire/remap.
    for check_id in (BUS_RETIRED_ID, 852, 844, 848, 853, 854):
        n = bind.execute(
            text("SELECT COUNT(*) FROM listings WHERE category_id = :id"),
            {"id": check_id},
        ).scalar()
        if int(n or 0) > 0:
            raise RuntimeError(
                f"Rental V2 blocked: listings exist on category_id={check_id} "
                f"(count={n}). Preserve compatibility before consolidating."
            )

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

    # Bus consolidation: rename/reuse 845.
    bus_row = bind.execute(
        text("SELECT id, slug FROM categories WHERE id = :id"),
        {"id": BUS_COMBINED_ID},
    ).fetchone()
    if bus_row is None:
        raise RuntimeError(f"Missing bus combined id={BUS_COMBINED_ID}")
    conflict = bind.execute(
        text("SELECT id FROM categories WHERE slug = :s AND id <> :id"),
        {"s": BUS_COMBINED_SLUG, "id": BUS_COMBINED_ID},
    ).fetchone()
    if conflict is not None:
        raise RuntimeError(
            f"Slug {BUS_COMBINED_SLUG} already used by id={conflict[0]}"
        )
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
            "slug": BUS_COMBINED_SLUG,
            "label": BUS_COMBINED_LABEL,
            "sort": RENTAL_LEAF_SORT[BUS_COMBINED_SLUG],
            "id": BUS_COMBINED_ID,
        },
    )

    # Remap retired bus 846 → 845 (0 listings expected).
    bind.execute(
        text(
            """
            UPDATE listings
            SET category_id = :tid, updated_at = now()
            WHERE category_id = :sid
            """
        ),
        {"tid": BUS_COMBINED_ID, "sid": BUS_RETIRED_ID},
    )
    bind.execute(
        text(
            """
            UPDATE categories
            SET is_active = false, updated_at = now()
            WHERE id = :id
            """
        ),
        {"id": BUS_RETIRED_ID},
    )

    # Ensure all final leaves.
    for slug in RENTAL_LEAF_SLUGS:
        if slug == BUS_COMBINED_SLUG:
            continue
        _ensure_leaf(
            bind,
            parent_id=parent_id,
            slug=slug,
            label=RENTAL_LEAF_LABELS[slug],
            sort=RENTAL_LEAF_SORT[slug],
            expected_id=RENTAL_LEAF_EXPECTED_IDS.get(slug),
        )

    # Inactive legacy.
    for slug in RENTAL_INACTIVE_LEGACY_SLUGS:
        if slug in {BUS_COMBINED_SLUG, BUS_COMBINED_OLD_SLUG}:
            # old microbus slug gone after rename
            if slug == BUS_COMBINED_OLD_SLUG:
                continue
        bind.execute(
            text(
                """
                UPDATE categories
                SET is_active = false, updated_at = now()
                WHERE slug = :slug AND is_active = true
                """
            ),
            {"slug": slug},
        )

    # Remaps for any leftover slug targets.
    for source_slug, target_slug in RENTAL_REMAP_TARGETS.items():
        src = bind.execute(
            text("SELECT id FROM categories WHERE slug = :s"),
            {"s": source_slug},
        ).fetchone()
        tgt = bind.execute(
            text("SELECT id FROM categories WHERE slug = :s"),
            {"s": target_slug},
        ).fetchone()
        if src is None or tgt is None:
            continue
        if int(src[0]) == int(tgt[0]):
            continue
        bind.execute(
            text(
                """
                UPDATE listings
                SET category_id = :tid, updated_at = now()
                WHERE category_id = :sid
                """
            ),
            {"tid": int(tgt[0]), "sid": int(src[0])},
        )

    def _upsert_alias(alias: str, target_slug: str, *, weight: int = 100) -> None:
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

    for alias, leaf_slug in RENTAL_LEAF_ALIASES.items():
        _upsert_alias(alias, leaf_slug)
    for alias, parent_slug in RENTAL_PARENT_ALIASES.items():
        _upsert_alias(alias, parent_slug, weight=80)
    for alias, svc_slug in RENTAL_SERVICE_BOUNDARY_ALIASES.items():
        _upsert_alias(alias, svc_slug, weight=120)

    # Parent no longer live Create/Search SoT.
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

    for slug, fields in RENTAL_CORE_FIELDS_BY_SLUG.items():
        row = bind.execute(
            text("SELECT id FROM categories WHERE slug = :s"),
            {"s": slug},
        ).fetchone()
        if row is None:
            raise RuntimeError(f"Missing rental leaf after ensure: {slug}")
        cid = int(row[0])
        bind.execute(
            text("DELETE FROM category_core_fields WHERE category_id = :cid"),
            {"cid": cid},
        )
        bind.execute(
            text("DELETE FROM category_optional_fields WHERE category_id = :cid"),
            {"cid": cid},
        )
        bind.execute(
            text("DELETE FROM category_filters WHERE category_id = :cid"),
            {"cid": cid},
        )
        for key, label, ftype, required, sort, options, hint in fields:
            ftype_val = ftype.value if hasattr(ftype, "value") else str(ftype)
            opts_json = (
                json.dumps(options, ensure_ascii=False) if options else None
            )
            bind.execute(
                text(
                    """
                    INSERT INTO category_core_fields
                    (category_id, field_key, label, field_type, is_required,
                     sort_order, options, ai_hint, create_intent,
                     created_at, updated_at)
                    VALUES
                    (:cid, :key, :label,
                     CAST(:ftype AS category_field_type_enum),
                     :req, :sort, CAST(:opts AS jsonb), :hint, NULL,
                     now(), now())
                    """
                ),
                {
                    "cid": cid,
                    "key": key,
                    "label": label,
                    "ftype": ftype_val,
                    "req": required,
                    "sort": sort,
                    "opts": opts_json,
                    "hint": hint,
                },
            )
        for key, label, ftype, sort, config in RENTAL_SEARCH_FILTERS_BY_SLUG[slug]:
            ftype_val = ftype.value if hasattr(ftype, "value") else str(ftype)
            cfg_json = (
                json.dumps(config, ensure_ascii=False) if config else None
            )
            bind.execute(
                text(
                    """
                    INSERT INTO category_filters
                    (category_id, filter_key, label, filter_type, sort_order,
                     config, search_intent, created_at, updated_at)
                    VALUES
                    (:cid, :key, :label,
                     CAST(:ftype AS category_filter_type_enum),
                     :sort, CAST(:cfg AS jsonb), '', now(), now())
                    """
                ),
                {
                    "cid": cid,
                    "key": key,
                    "label": label,
                    "ftype": ftype_val,
                    "sort": sort,
                    "cfg": cfg_json,
                },
            )

    # Sanity: exactly 9 active children under rental parent.
    active_n = bind.execute(
        text(
            """
            SELECT COUNT(*) FROM categories
            WHERE parent_id = :pid AND is_active = true
            """
        ),
        {"pid": parent_id},
    ).scalar()
    if int(active_n or 0) != 9:
        raise RuntimeError(
            f"Rental V2 expected 9 active children; got {active_n}"
        )


def downgrade() -> None:
    # Non-destructive: do not restore old Rental SoT automatically.
    pass
