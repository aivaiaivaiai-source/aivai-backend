"""Water Transport Sale V2: 6 leaves + boat_motor catalog + cleanups.

Revision ID: g7b8c9d0e1f2waterv2
Revises: f6a7b8c9d0e1cargov2
Create Date: 2026-11-03

- Activate existing Boat Motor 817 under Water parent 692
- Seed leaf core_fields + filters for 6 active Water sale leaves
- Parent picker-only (drop thin parent SoT)
- Add vehicle_type boat_motor + clean typed sale catalog
- Disable Jet Ski model-as-brand pollution brands
- Disable Other Watercraft engine-manufacturer craft brands
- Upsert Другая марка per typed water vehicle_type
- Do NOT create Kayak/Canoe/SUP/Water Bike / Boat Trailer leaves
- Do NOT reactivate inflatable leaf
"""
from __future__ import annotations

import json

from alembic import op
from sqlalchemy import text

from app.seeds.water_sale_v2 import (
    BOAT_MOTOR_BRANDS,
    BOAT_MOTOR_MODELS,
    JET_SKI_CLEAN_MODELS,
    JET_SKI_DISABLE_BRAND_SLUGS,
    OTHER_WATERCRAFT_DISABLE_BRAND_SLUGS,
    WATER_CORE_FIELDS_BY_SLUG,
    WATER_INACTIVE_LEGACY_SLUGS,
    WATER_LEAF_ALIASES,
    WATER_LEAF_LABELS,
    WATER_LEAF_SORT,
    WATER_PARENT_ALIASES,
    WATER_PARENT_SLUG,
    WATER_SEARCH_FILTERS_BY_SLUG,
    water_other_brands,
    water_other_models,
)

revision = "g7b8c9d0e1f2waterv2"
down_revision = "f6a7b8c9d0e1cargov2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    # Postgres: new enum labels cannot be used in the same transaction as ADD VALUE.
    if bind.dialect.name == "postgresql":
        with op.get_context().autocommit_block():
            op.execute(
                "ALTER TYPE vehicle_type_enum ADD VALUE IF NOT EXISTS 'boat_motor'"
            )

    parent = bind.execute(
        text("SELECT id FROM categories WHERE slug = :s"),
        {"s": WATER_PARENT_SLUG},
    ).fetchone()
    if parent is None:
        raise RuntimeError(f"Missing parent {WATER_PARENT_SLUG}")
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

    for slug, label in WATER_LEAF_LABELS.items():
        sort = WATER_LEAF_SORT[slug]
        row = bind.execute(
            text("SELECT id FROM categories WHERE slug = :s"),
            {"s": slug},
        ).fetchone()
        if row is None:
            raise RuntimeError(f"Water leaf missing: {slug}")
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

    # Explicit Boat Motor identity check (reuse 817 — do not insert new).
    motor = bind.execute(
        text(
            """
            SELECT id, parent_id, is_active
            FROM categories
            WHERE slug = 'transport-watercraft-lodochnye-motory'
            """
        )
    ).fetchone()
    if motor is None or int(motor[0]) != 817:
        raise RuntimeError(
            f"Boat Motor must reuse id=817; got {motor}"
        )
    if int(motor[1]) != parent_id:
        raise RuntimeError(
            f"Boat Motor parent must be {parent_id}; got {motor[1]}"
        )

    for slug in WATER_INACTIVE_LEGACY_SLUGS:
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

    for alias, leaf_slug in WATER_LEAF_ALIASES.items():
        _upsert_alias(alias, leaf_slug)
    for alias, parent_slug in WATER_PARENT_ALIASES.items():
        _upsert_alias(alias, parent_slug, weight=80)

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

    for slug, fields in WATER_CORE_FIELDS_BY_SLUG.items():
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
        for key, label, ftype, sort, config in WATER_SEARCH_FILTERS_BY_SLUG[slug]:
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

    for slug, name, country, vtype in BOAT_MOTOR_BRANDS:
        _upsert_brand(slug, name, country, vtype.value)
    for brand_slug, models in BOAT_MOTOR_MODELS.items():
        _upsert_models(brand_slug, models)

    for slug, name, country, vtype_str in water_other_brands():
        _upsert_brand(slug, name, country, vtype_str)
    for brand_slug, models in water_other_models().items():
        _upsert_models(brand_slug, models)

    for brand_slug, models in JET_SKI_CLEAN_MODELS.items():
        _upsert_models(brand_slug, models)

    for bad_slug in (
        *JET_SKI_DISABLE_BRAND_SLUGS,
        *OTHER_WATERCRAFT_DISABLE_BRAND_SLUGS,
    ):
        bind.execute(
            text(
                """
                UPDATE vehicle_brands
                SET is_enabled = false, updated_at = now()
                WHERE slug = :slug
                """
            ),
            {"slug": bad_slug},
        )


def downgrade() -> None:
    # Non-destructive: keep leaf schemas and boat_motor enum value.
    pass
