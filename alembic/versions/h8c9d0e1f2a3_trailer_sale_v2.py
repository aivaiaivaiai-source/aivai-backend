"""Trailers Sale V2: 3 leaves + remaps + Other Brand.

Revision ID: h8c9d0e1f2a3trailerv2
Revises: g7b8c9d0e1f2waterv2
Create Date: 2026-11-03

- Preserve parent 693 + leaves 1226/824/1227
- Unique sort_order: Прицепы 10, Полуприцепы 20, Жилые 30
- Specialty L3 + water/farm trailer leaves stay inactive
- Retarget remaps 818/840 → 1226 (policy in transport_v2_1)
- Seed leaf core_fields + filters; clear parent SoT
- Upsert Другая марка for drawbar/semi/camper
- No new L3
"""
from __future__ import annotations

import json

from alembic import op
from sqlalchemy import text

from app.seeds.trailer_sale_v2 import (
    TRAILER_CORE_FIELDS_BY_SLUG,
    TRAILER_INACTIVE_LEGACY_SLUGS,
    TRAILER_LEAF_ALIASES,
    TRAILER_LEAF_LABELS,
    TRAILER_LEAF_SORT,
    TRAILER_PARENT_ALIASES,
    TRAILER_PARENT_SLUG,
    TRAILER_REMAP_TARGETS,
    TRAILER_SEARCH_FILTERS_BY_SLUG,
    trailer_other_brands,
    trailer_other_models,
)

revision = "h8c9d0e1f2a3trailerv2"
down_revision = "g7b8c9d0e1f2waterv2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    parent = bind.execute(
        text("SELECT id FROM categories WHERE slug = :s"),
        {"s": TRAILER_PARENT_SLUG},
    ).fetchone()
    if parent is None:
        raise RuntimeError(f"Missing parent {TRAILER_PARENT_SLUG}")
    parent_id = int(parent[0])

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

    expected_ids = {
        "transport-trailers-pritsepy": 1226,
        "transport-trailers-polupritsepy": 824,
        "transport-trailers-zhilye-pritsepy-kempery": 1227,
    }
    for slug, label in TRAILER_LEAF_LABELS.items():
        sort = TRAILER_LEAF_SORT[slug]
        row = bind.execute(
            text("SELECT id FROM categories WHERE slug = :s"),
            {"s": slug},
        ).fetchone()
        if row is None:
            raise RuntimeError(f"Trailer leaf missing: {slug}")
        leaf_id = int(row[0])
        expected = expected_ids.get(slug)
        if expected is not None and leaf_id != expected:
            raise RuntimeError(
                f"Trailer leaf {slug} must reuse id={expected}; got {leaf_id}"
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
                WHERE slug = :slug
                """
            ),
            {
                "pid": parent_id,
                "label": label,
                "sort": sort,
                "slug": slug,
            },
        )

    for slug in TRAILER_INACTIVE_LEGACY_SLUGS:
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

    # Retarget any listing still on remapped inactive sources (audit: 0).
    for source_slug, target_slug in TRAILER_REMAP_TARGETS.items():
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
                {"cid": cid, "alias": alias, "w": weight, "id": int(existing[0])},
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

    for alias, leaf_slug in TRAILER_LEAF_ALIASES.items():
        _upsert_alias(alias, leaf_slug)
    for alias, parent_slug in TRAILER_PARENT_ALIASES.items():
        _upsert_alias(alias, parent_slug, weight=80)

    # Parent no longer live Create/Search SoT (incl. payload_kg).
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

    for slug, fields in TRAILER_CORE_FIELDS_BY_SLUG.items():
        row = bind.execute(
            text("SELECT id FROM categories WHERE slug = :s"),
            {"s": slug},
        ).fetchone()
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
            opts_json = json.dumps(options, ensure_ascii=False) if options else None
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
        for key, label, ftype, sort, config in TRAILER_SEARCH_FILTERS_BY_SLUG[slug]:
            ftype_val = ftype.value if hasattr(ftype, "value") else str(ftype)
            cfg_json = json.dumps(config, ensure_ascii=False) if config else None
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
                    "cid": cid,
                    "key": key,
                    "label": label,
                    "ftype": ftype_val,
                    "sort": sort,
                    "cfg": cfg_json,
                },
            )

    def _upsert_brand(slug: str, name: str, country: str | None, vtype_val: str) -> None:
        existing = bind.execute(
            text("SELECT id FROM vehicle_brands WHERE slug = :s"),
            {"s": slug},
        ).fetchone()
        if existing is None:
            bind.execute(
                text(
                    """
                    INSERT INTO vehicle_brands
                    (slug, name, country_origin, vehicle_type, is_enabled,
                     created_at, updated_at)
                    VALUES
                    (:slug, :name, :country,
                     CAST(:vt AS vehicle_type_enum), true, now(), now())
                    """
                ),
                {
                    "slug": slug,
                    "name": name,
                    "country": country,
                    "vt": vtype_val,
                },
            )
        else:
            bind.execute(
                text(
                    """
                    UPDATE vehicle_brands
                    SET name = :name,
                        country_origin = :country,
                        vehicle_type = CAST(:vt AS vehicle_type_enum),
                        is_enabled = true,
                        updated_at = now()
                    WHERE slug = :slug
                    """
                ),
                {
                    "slug": slug,
                    "name": name,
                    "country": country,
                    "vt": vtype_val,
                },
            )

    def _upsert_models(brand_slug: str, models: list[tuple[str, str]]) -> None:
        brand = bind.execute(
            text("SELECT id FROM vehicle_brands WHERE slug = :s"),
            {"s": brand_slug},
        ).fetchone()
        if brand is None:
            return
        brand_id = int(brand[0])
        for model_slug, model_name in models:
            m = bind.execute(
                text(
                    """
                    SELECT id FROM vehicle_models
                    WHERE brand_id = :bid AND slug = :ms
                    """
                ),
                {"bid": brand_id, "ms": model_slug},
            ).fetchone()
            if m is None:
                bind.execute(
                    text(
                        """
                        INSERT INTO vehicle_models
                        (brand_id, slug, name, is_enabled, created_at, updated_at)
                        VALUES (:bid, :ms, :mn, true, now(), now())
                        """
                    ),
                    {"bid": brand_id, "ms": model_slug, "mn": model_name},
                )
            else:
                bind.execute(
                    text(
                        """
                        UPDATE vehicle_models
                        SET name = :mn, is_enabled = true, updated_at = now()
                        WHERE id = :id
                        """
                    ),
                    {"mn": model_name, "id": int(m[0])},
                )

    for slug, name, country, vtype_str in trailer_other_brands():
        _upsert_brand(slug, name, country, vtype_str)
    for brand_slug, models in trailer_other_models().items():
        _upsert_models(brand_slug, models)


def downgrade() -> None:
    # Non-destructive: keep leaf schemas.
    pass
