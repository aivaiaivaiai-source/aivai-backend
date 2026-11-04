"""Farm Machinery Sale V2: 7 leaves + implement consolidation.

Revision ID: i9d0e1f2a3b4farmv2
Revises: h8c9d0e1f2a3trailerv2
Create Date: 2026-11-03

- Preserve parent 694 + self-propelled IDs
- Reuse 839 as broad implement leaf (rename slug/label)
- Retire implement L3 without DELETE
- Seed leaf core_fields + filters; clear parent SoT
- Add farm_implement vehicle_type + Other Brand
- Disable polluted manufacturer identities for live picker
- Farm trailer 840 stays inactive → Trailers 1226
"""
from __future__ import annotations

import json

from alembic import op
from sqlalchemy import text

from app.seeds.farm_sale_v2 import (
    BROAD_IMPLEMENT_ID,
    BROAD_IMPLEMENT_LABEL,
    BROAD_IMPLEMENT_OLD_SLUG,
    BROAD_IMPLEMENT_SLUG,
    FARM_CORE_FIELDS_BY_SLUG,
    FARM_INACTIVE_LEGACY_SLUGS,
    FARM_LEAF_ALIASES,
    FARM_LEAF_EXPECTED_IDS,
    FARM_LEAF_LABELS,
    FARM_LEAF_SORT,
    FARM_PARENT_ALIASES,
    FARM_PARENT_SLUG,
    FARM_POLLUTED_BRAND_NAMES,
    FARM_REMAP_TARGETS,
    FARM_RETIRED_IMPLEMENT_MAP,
    FARM_SEARCH_FILTERS_BY_SLUG,
    farm_implement_brands,
    farm_other_brands,
    farm_other_models,
)

revision = "i9d0e1f2a3b4farmv2"
down_revision = "h8c9d0e1f2a3trailerv2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    # Postgres: new enum labels cannot be used in the same transaction as ADD VALUE.
    if bind.dialect.name == "postgresql":
        with op.get_context().autocommit_block():
            op.execute(
                "ALTER TYPE vehicle_type_enum ADD VALUE IF NOT EXISTS 'farm_implement'"
            )

    parent = bind.execute(
        text("SELECT id FROM categories WHERE slug = :s"),
        {"s": FARM_PARENT_SLUG},
    ).fetchone()
    if parent is None:
        raise RuntimeError(f"Missing parent {FARM_PARENT_SLUG}")
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

    # Rename/reuse 839 → broad implement leaf.
    old = bind.execute(
        text("SELECT id, slug FROM categories WHERE id = :id"),
        {"id": BROAD_IMPLEMENT_ID},
    ).fetchone()
    if old is None:
        raise RuntimeError(f"Missing broad implement id={BROAD_IMPLEMENT_ID}")
    if int(old[0]) != BROAD_IMPLEMENT_ID:
        raise RuntimeError("Broad implement id mismatch")
    # Ensure slug free / claim old slug row.
    conflict = bind.execute(
        text(
            "SELECT id FROM categories WHERE slug = :s AND id <> :id"
        ),
        {"s": BROAD_IMPLEMENT_SLUG, "id": BROAD_IMPLEMENT_ID},
    ).fetchone()
    if conflict is not None:
        raise RuntimeError(
            f"Slug {BROAD_IMPLEMENT_SLUG} already used by id={conflict[0]}"
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
            "slug": BROAD_IMPLEMENT_SLUG,
            "label": BROAD_IMPLEMENT_LABEL,
            "sort": FARM_LEAF_SORT[BROAD_IMPLEMENT_SLUG],
            "id": BROAD_IMPLEMENT_ID,
        },
    )

    for slug, label in FARM_LEAF_LABELS.items():
        if slug == BROAD_IMPLEMENT_SLUG:
            continue
        sort = FARM_LEAF_SORT[slug]
        row = bind.execute(
            text("SELECT id FROM categories WHERE slug = :s"),
            {"s": slug},
        ).fetchone()
        if row is None:
            raise RuntimeError(f"Farm leaf missing: {slug}")
        leaf_id = int(row[0])
        expected = FARM_LEAF_EXPECTED_IDS.get(slug)
        if expected is not None and leaf_id != expected:
            raise RuntimeError(
                f"Farm leaf {slug} must reuse id={expected}; got {leaf_id}"
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

    # Retire implement L3 + legacy umbrellas (keep historical IDs).
    for slug in FARM_INACTIVE_LEGACY_SLUGS:
        if slug in {BROAD_IMPLEMENT_SLUG, BROAD_IMPLEMENT_OLD_SLUG}:
            # old slug no longer exists after rename; ignore
            if slug == BROAD_IMPLEMENT_OLD_SLUG:
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

    # Explicitly keep 840 inactive.
    bind.execute(
        text(
            """
            UPDATE categories
            SET is_active = false, updated_at = now()
            WHERE id = 840
            """
        )
    )

    # Retarget listings on remapped sources (audit: 0).
    for source_slug, target_slug in FARM_REMAP_TARGETS.items():
        src = bind.execute(
            text("SELECT id FROM categories WHERE slug = :s"),
            {"s": source_slug},
        ).fetchone()
        tgt = bind.execute(
            text("SELECT id FROM categories WHERE slug = :s"),
            {"s": target_slug},
        ).fetchone()
        if src is None or tgt is None:
            # old broad slug after rename: map by id for retired that pointed to 839
            if source_slug == BROAD_IMPLEMENT_OLD_SLUG:
                continue
            # retired implement still has its slug
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

    for alias, leaf_slug in FARM_LEAF_ALIASES.items():
        _upsert_alias(alias, leaf_slug)
    for alias, parent_slug in FARM_PARENT_ALIASES.items():
        _upsert_alias(alias, parent_slug, weight=80)

    # Parent no longer live Create/Search SoT (incl. hours/powertrain).
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

    for slug, fields in FARM_CORE_FIELDS_BY_SLUG.items():
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
            text(
                "DELETE FROM category_optional_fields WHERE category_id = :cid"
            ),
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
        for key, label, ftype, sort, config in FARM_SEARCH_FILTERS_BY_SLUG[slug]:
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

    def _upsert_brand(
        slug: str, name: str, country: str | None, vtype_val: str
    ) -> None:
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
                        country_origin = COALESCE(:country, country_origin),
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
                    {
                        "bid": brand_id,
                        "ms": model_slug,
                        "mn": model_name,
                    },
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

    for slug, name, country, vtype_str in farm_other_brands():
        _upsert_brand(slug, name, country, vtype_str)
    for brand_slug, models in farm_other_models().items():
        _upsert_models(brand_slug, models)

    for slug, name, country, vtype_str in farm_implement_brands():
        _upsert_brand(slug, name, country, vtype_str)

    # Disable polluted manufacturer identities from live picker (keep rows).
    farm_vts = (
        "tractor",
        "mini_tractor",
        "walk_behind",
        "combine",
        "seeder",
        "plow",
        "harrow",
        "cultivator",
        "hiller",
        "ditcher",
        "mulcher",
        "mower",
        "walk_behind_mower",
        "baler",
        "header",
        "rake",
        "feed_mixer",
        "sprayer",
        "fertilizer_spreader",
        "manure_spreader",
        "potato_planter",
        "potato_digger",
        "kun",
        "farm_crusher",
        "grain_thrower",
        "grain_cleaner",
        "film_layer",
        "ridge_former",
        "agri_drone",
        "other_agri",
        "agricultural",
        "tillage",
        "forage",
        "farm_implement",
    )
    for name in FARM_POLLUTED_BRAND_NAMES:
        bind.execute(
            text(
                """
                UPDATE vehicle_brands
                SET is_enabled = false, updated_at = now()
                WHERE name = :name
                  AND vehicle_type::text IN (
                    'tractor', 'mini_tractor', 'walk_behind', 'combine',
                    'seeder', 'plow', 'harrow', 'cultivator', 'hiller',
                    'ditcher', 'mulcher', 'mower', 'walk_behind_mower',
                    'baler', 'header', 'rake', 'feed_mixer', 'sprayer',
                    'fertilizer_spreader', 'manure_spreader', 'potato_planter',
                    'potato_digger', 'kun', 'farm_crusher', 'grain_thrower',
                    'grain_cleaner', 'film_layer', 'ridge_former',
                    'agri_drone', 'other_agri', 'agricultural', 'tillage',
                    'forage', 'farm_implement'
                  )
                  AND is_enabled = true
                """
            ),
            {"name": name},
        )
    _ = farm_vts

    # Silence unused import lint for mapping used in report/docs.
    _ = FARM_RETIRED_IMPLEMENT_MAP


def downgrade() -> None:
    # Non-destructive: keep leaf schemas / renamed broad leaf.
    pass
