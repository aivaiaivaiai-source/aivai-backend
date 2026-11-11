"""Animals V2 Package A — Services vet ownership + Create SoT.

Revision ID: q6f7a8b9c0d1animalpa
Revises: p5e6f7a8b9c0animaltax
Create Date: 2026-11-11

- Expand Services «прочие» with exact vet/grooming kinds (Option B)
- Soft-retire animals-veterinarnye-uslugi (0 listings required)
- Seed Animals Package A Create cores on 15 active L2
- Root remains picker-only
- Does NOT seed Package B Search filters
"""
from __future__ import annotations

import json

from alembic import op
from sqlalchemy import text

revision = "q6f7a8b9c0d1animalpa"
down_revision = "p5e6f7a8b9c0animaltax"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from app.seeds.animals_v2 import (
        ANIMALS_ROOT_SLUG,
        ANIMALS_V2_CANONICAL_LEAVES,
        ANIMALS_V2_CANONICAL_SLUGS,
        ANIMALS_V2_EXPECTED_L2_COUNT,
        ANIMALS_VET_SERVICES_SLUG,
        animals_v2_assert_package_a_contracts,
        build_animals_v2_core_fields,
    )
    from app.seeds.services_v2 import build_services_v2_core_fields

    animals_v2_assert_package_a_contracts()
    bind = op.get_bind()

    root = bind.execute(
        text("SELECT id FROM categories WHERE slug = :slug"),
        {"slug": ANIMALS_ROOT_SLUG},
    ).fetchone()
    if root is None:
        raise RuntimeError("animals root missing")
    root_id = int(root[0])

    vet = bind.execute(
        text("SELECT id FROM categories WHERE slug = :slug"),
        {"slug": ANIMALS_VET_SERVICES_SLUG},
    ).fetchone()
    if vet is not None:
        vet_id = int(vet[0])
        n_vet = bind.execute(
            text("SELECT count(*) FROM listings WHERE category_id = :cid"),
            {"cid": vet_id},
        ).scalar_one()
        if int(n_vet or 0) > 0:
            raise RuntimeError(
                f"Animals Package A STOP: vet-services listings exist ({n_vet})"
            )
        bind.execute(
            text(
                "UPDATE categories SET is_active = false, updated_at = now() "
                "WHERE id = :id"
            ),
            {"id": vet_id},
        )
        for table in (
            "category_core_fields",
            "category_optional_fields",
            "category_filters",
        ):
            bind.execute(
                text(f"DELETE FROM {table} WHERE category_id = :cid"),
                {"cid": vet_id},
            )

    bind.execute(
        text(
            "UPDATE categories SET is_active = true, parent_id = NULL, "
            "updated_at = now() WHERE id = :id"
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

    slug_to_id: dict[str, int] = {}
    for label, slug, sort_order in ANIMALS_V2_CANONICAL_LEAVES:
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
                      (:pid, :slug, :name, 'animal', true, :sort, true, now(), now())
                    """
                ),
                {
                    "pid": root_id,
                    "slug": slug,
                    "name": label,
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
                        sort_order = :sort, entity_type = 'animal',
                        requires_city = true, updated_at = now()
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

    children = bind.execute(
        text("SELECT id, slug FROM categories WHERE parent_id = :pid"),
        {"pid": root_id},
    ).fetchall()
    for cid, slug in children:
        if slug in ANIMALS_V2_CANONICAL_SLUGS:
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

    services_cores = build_services_v2_core_fields()
    other_slug = "services-prochie-uslugi"
    other = bind.execute(
        text("SELECT id FROM categories WHERE slug = :slug"),
        {"slug": other_slug},
    ).fetchone()
    if other is None:
        raise RuntimeError("services-prochie-uslugi missing")
    if other_slug not in services_cores:
        raise RuntimeError("Services other leaf missing from builder")
    _seed_cores(int(other[0]), services_cores[other_slug])

    for slug, fields in build_animals_v2_core_fields().items():
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
    if int(active or 0) != ANIMALS_V2_EXPECTED_L2_COUNT:
        raise RuntimeError(
            f"Animals V2 Package A STOP: expected "
            f"{ANIMALS_V2_EXPECTED_L2_COUNT} active L2, got {active}"
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
    if int(nonempty or 0) != ANIMALS_V2_EXPECTED_L2_COUNT:
        raise RuntimeError(
            f"Animals V2 Package A STOP: expected cores on all active L2, "
            f"got nonempty={nonempty}"
        )


def downgrade() -> None:
    pass
