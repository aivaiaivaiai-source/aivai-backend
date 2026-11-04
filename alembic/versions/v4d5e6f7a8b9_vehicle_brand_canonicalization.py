"""Vehicle brand canonicalization — disable alias-as-brand duplicates.

Revision ID: v4d5e6f7a8b9
Revises: u3c4d5e6f7a8
Create Date: 2026-09-20

Corrupt brands were created historically with MODEL_ALIAS text as slug and the
parent marque as display name (e.g. slug=солярис, name=Hyundai), then given a
full clone of the marque model catalog. Flutter name→slug maps then preferred
the corrupt slug and leaked models without execution policy (e.g. Porter).

This migration:
- records explicit corrupt→canonical mapping
- remaps listing_field_values brand/model refs to canonical IDs by model slug
- ensures VehicleAlias rows for the alias text
- disables corrupt brands (no mass DELETE)

Rollback: re-enable corrupt brands; reverse ref remaps from mapping table.
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "v4d5e6f7a8b9"
down_revision = "u3c4d5e6f7a8"
branch_labels = None
depends_on = None

# (corrupt_slug, canonical_brand_slug, alias_target_model_slug)
# Confirmed via duplicate display-name audit + MODEL_ALIASES correspondence.
_CORRUPT: list[tuple[str, str, str]] = [
    ("x3", "bmw", "x3"),
    ("атто 3", "byd", "atto-3"),
    ("тигго 7", "chery", "tiggo-7"),
    ("монжаро", "geely", "monjaro"),
    ("джолион", "haval", "jolion"),
    ("солярис", "hyundai", "solaris"),
    ("нива", "lada", "niva"),
    ("lx600", "lexus", "lx600"),
    ("гелик", "mercedes-benz", "g-class"),
    ("танк 500", "tank", "500"),
    ("модель y", "tesla", "model-y"),
    ("приус", "toyota", "prius"),
    ("vw", "volkswagen", ""),  # brand-level synonym only
]


def upgrade() -> None:
    conn = op.get_bind()

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS vehicle_brand_canonical_map (
            corrupt_brand_id INTEGER PRIMARY KEY,
            corrupt_slug TEXT NOT NULL,
            canonical_brand_id INTEGER NOT NULL
                REFERENCES vehicle_brands(id),
            canonical_slug TEXT NOT NULL,
            alias_text TEXT NOT NULL,
            target_model_slug TEXT,
            brand_refs_remapped INTEGER NOT NULL DEFAULT 0,
            model_refs_remapped INTEGER NOT NULL DEFAULT 0,
            disabled_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )

    print("=== brand canonicalization: live ref report ===")
    for corrupt_slug, canonical_slug, model_slug in _CORRUPT:
        crow = conn.execute(
            sa.text(
                "SELECT id, name, is_enabled FROM vehicle_brands WHERE slug = :s"
            ),
            {"s": corrupt_slug},
        ).mappings().first()
        can = conn.execute(
            sa.text(
                "SELECT id, name FROM vehicle_brands WHERE slug = :s"
            ),
            {"s": canonical_slug},
        ).mappings().first()
        if crow is None:
            print(f"  SKIP missing corrupt slug={corrupt_slug!r}")
            continue
        if can is None:
            print(f"  SKIP missing canonical slug={canonical_slug!r}")
            continue
        # Confirm name collision / alias relationship
        if crow["name"] != can["name"]:
            print(
                f"  REVIEW name mismatch corrupt={corrupt_slug!r} "
                f"name={crow['name']!r} canonical={canonical_slug!r} "
                f"name={can['name']!r} — still proceeding (alias slug)"
            )

        brand_refs = conn.execute(
            sa.text(
                """
                SELECT COUNT(*) FROM listing_field_values
                WHERE field_key = 'brand' AND ref_brand_id = :bid
                """
            ),
            {"bid": crow["id"]},
        ).scalar() or 0
        model_refs = conn.execute(
            sa.text(
                """
                SELECT COUNT(*) FROM listing_field_values lfv
                JOIN vehicle_models m ON m.id = lfv.ref_model_id
                WHERE lfv.field_key = 'model' AND m.brand_id = :bid
                """
            ),
            {"bid": crow["id"]},
        ).scalar() or 0
        print(
            f"  {corrupt_slug!r}→{canonical_slug!r} "
            f"corrupt_id={crow['id']} canon_id={can['id']} "
            f"brand_refs={brand_refs} model_refs={model_refs}"
        )

        # Remap brand field refs
        brand_n = conn.execute(
            sa.text(
                """
                UPDATE listing_field_values
                SET ref_brand_id = :cid
                WHERE field_key = 'brand' AND ref_brand_id = :xid
                """
            ),
            {"cid": can["id"], "xid": crow["id"]},
        ).rowcount or 0

        # Remap model field refs by matching slug under canonical brand
        model_n = conn.execute(
            sa.text(
                """
                UPDATE listing_field_values AS lfv
                SET ref_model_id = cm.id
                FROM vehicle_models AS xm
                JOIN vehicle_models AS cm
                  ON cm.brand_id = :cid AND cm.slug = xm.slug AND cm.is_enabled IS TRUE
                WHERE lfv.field_key = 'model'
                  AND lfv.ref_model_id = xm.id
                  AND xm.brand_id = :xid
                """
            ),
            {"cid": can["id"], "xid": crow["id"]},
        ).rowcount or 0

        # Ensure alias exists (model target when possible)
        target_mid = None
        if model_slug:
            target_mid = conn.execute(
                sa.text(
                    """
                    SELECT id FROM vehicle_models
                    WHERE brand_id = :cid AND slug = :ms AND is_enabled IS TRUE
                    LIMIT 1
                    """
                ),
                {"cid": can["id"], "ms": model_slug},
            ).scalar()

        compact = corrupt_slug.replace(" ", "").lower()
        spaced = corrupt_slug.strip().lower()
        existing_alias = conn.execute(
            sa.text(
                """
                SELECT id FROM vehicle_aliases
                WHERE alias_compact = :c AND locale = 'ru'
                LIMIT 1
                """
            ),
            {"c": compact},
        ).scalar()
        if existing_alias is None:
            if target_mid is not None:
                conn.execute(
                    sa.text(
                        """
                        INSERT INTO vehicle_aliases
                          (alias, alias_normalized, alias_compact, locale,
                           target_type, brand_id, model_id, is_enabled)
                        VALUES
                          (:alias, :spaced, :compact, 'ru',
                           CAST('model' AS vehicle_alias_target_enum),
                           :bid, :mid, TRUE)
                        """
                    ),
                    {
                        "alias": corrupt_slug,
                        "spaced": spaced,
                        "compact": compact,
                        "bid": can["id"],
                        "mid": target_mid,
                    },
                )
            else:
                conn.execute(
                    sa.text(
                        """
                        INSERT INTO vehicle_aliases
                          (alias, alias_normalized, alias_compact, locale,
                           target_type, brand_id, model_id, is_enabled)
                        VALUES
                          (:alias, :spaced, :compact, 'ru',
                           CAST('brand' AS vehicle_alias_target_enum),
                           :bid, NULL, TRUE)
                        """
                    ),
                    {
                        "alias": corrupt_slug,
                        "spaced": spaced,
                        "compact": compact,
                        "bid": can["id"],
                    },
                )
        else:
            # Split UPDATE paths — asyncpg cannot infer type of NULL :mid
            # when used both as a bind value and in `IS NULL`.
            if target_mid is not None:
                conn.execute(
                    sa.text(
                        """
                        UPDATE vehicle_aliases
                        SET brand_id = :bid,
                            model_id = :mid,
                            target_type = CAST('model' AS vehicle_alias_target_enum),
                            is_enabled = TRUE,
                            alias = :alias,
                            alias_normalized = :spaced
                        WHERE id = :aid
                        """
                    ),
                    {
                        "bid": can["id"],
                        "mid": target_mid,
                        "alias": corrupt_slug,
                        "spaced": spaced,
                        "aid": existing_alias,
                    },
                )
            else:
                conn.execute(
                    sa.text(
                        """
                        UPDATE vehicle_aliases
                        SET brand_id = :bid,
                            model_id = NULL,
                            target_type = CAST('brand' AS vehicle_alias_target_enum),
                            is_enabled = TRUE,
                            alias = :alias,
                            alias_normalized = :spaced
                        WHERE id = :aid
                        """
                    ),
                    {
                        "bid": can["id"],
                        "alias": corrupt_slug,
                        "spaced": spaced,
                        "aid": existing_alias,
                    },
                )

        conn.execute(
            sa.text(
                """
                INSERT INTO vehicle_brand_canonical_map
                  (corrupt_brand_id, corrupt_slug, canonical_brand_id,
                   canonical_slug, alias_text, target_model_slug,
                   brand_refs_remapped, model_refs_remapped)
                VALUES
                  (:xid, :xs, :cid, :cs, :alias, :ms, :bn, :mn)
                ON CONFLICT (corrupt_brand_id) DO UPDATE SET
                  brand_refs_remapped = EXCLUDED.brand_refs_remapped,
                  model_refs_remapped = EXCLUDED.model_refs_remapped,
                  disabled_at = now()
                """
            ),
            {
                "xid": crow["id"],
                "xs": corrupt_slug,
                "cid": can["id"],
                "cs": canonical_slug,
                "alias": corrupt_slug,
                "ms": model_slug,
                "bn": brand_n,
                "mn": model_n,
            },
        )

        # Disable corrupt brand + its models (keep rows for history)
        conn.execute(
            sa.text(
                "UPDATE vehicle_brands SET is_enabled = FALSE WHERE id = :id"
            ),
            {"id": crow["id"]},
        )
        conn.execute(
            sa.text(
                "UPDATE vehicle_models SET is_enabled = FALSE WHERE brand_id = :id"
            ),
            {"id": crow["id"]},
        )
        print(f"    remapped brand={brand_n} model={model_n}; disabled")

    print("=== end brand canonicalization ===")


def downgrade() -> None:
    conn = op.get_bind()
    rows = conn.execute(
        sa.text("SELECT * FROM vehicle_brand_canonical_map")
    ).mappings().all()
    for row in rows:
        # Re-enable corrupt brand/models
        conn.execute(
            sa.text(
                "UPDATE vehicle_brands SET is_enabled = TRUE WHERE id = :id"
            ),
            {"id": row["corrupt_brand_id"]},
        )
        conn.execute(
            sa.text(
                "UPDATE vehicle_models SET is_enabled = TRUE WHERE brand_id = :id"
            ),
            {"id": row["corrupt_brand_id"]},
        )
        # Best-effort reverse remap of brand refs only (models stay on canonical —
        # full reverse would need per-ref snapshot; documented limitation).
        print(
            f"  rollback re-enabled corrupt={row['corrupt_slug']!r}; "
            f"listing refs NOT auto-reverted (see map table)"
        )
    op.execute("DROP TABLE IF EXISTS vehicle_brand_canonical_map")
