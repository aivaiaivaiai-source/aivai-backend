"""Vehicle execution foundation V2.

Revision ID: u3c4d5e6f7a8
Revises: t2b3c4d5e6f7
Create Date: 2026-09-20

Adds:
- vehicle_execution_enum
- vehicle_model_allowed_executions
- listings.vehicle_execution
- seeds approved dual/cargo-only model executions (idempotent)

Safety:
- Does NOT delete models or listings.
- Does NOT remap historical listing field refs.
- Does NOT invent vehicle_execution for existing listings (left NULL).
- Prints a pre-seed reference report (listing/draft counts per model).

Rollback:
  alembic downgrade t2b3c4d5e6f7
  → drops listings.vehicle_execution + vehicle_model_allowed_executions + enum.
  Historical listing field brand/model refs remain intact.
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "u3c4d5e6f7a8"
down_revision = "t2b3c4d5e6f7"
branch_labels = None
depends_on = None

_SEED: list[tuple[str, str, tuple[str, ...]]] = [
    ("mercedes-benz", "sprinter", ("cargo", "passenger")),
    ("gaz", "gazelle", ("cargo", "passenger")),
    ("gaz", "sobol", ("cargo", "passenger")),
    ("ford", "transit", ("cargo", "passenger")),
    ("toyota", "hiace", ("cargo", "passenger")),
    ("hyundai", "porter", ("cargo",)),
    ("kia", "bongo", ("cargo",)),
    ("iveco", "daily", ("cargo",)),
    ("fiat", "ducato", ("cargo",)),
    ("citroen", "jumper", ("cargo",)),
    ("uaz", "profi", ("cargo",)),
]


def _report_live_refs(conn) -> None:
    print("=== vehicle_execution foundation: live ref report ===")
    for brand_slug, model_slug, _ex in _SEED:
        row = conn.execute(
            sa.text(
                """
                SELECT m.id AS model_id,
                       COUNT(lfv.id) FILTER (
                         WHERE l.status = 'active'
                       ) AS active_refs,
                       COUNT(lfv.id) FILTER (
                         WHERE l.status = 'draft'
                       ) AS draft_refs,
                       COUNT(lfv.id) AS total_refs
                FROM vehicle_models m
                JOIN vehicle_brands b ON b.id = m.brand_id
                LEFT JOIN listing_field_values lfv
                  ON lfv.ref_model_id = m.id AND lfv.field_key = 'model'
                LEFT JOIN listings l ON l.id = lfv.listing_id
                WHERE b.slug = :bs AND m.slug = :ms
                GROUP BY m.id
                """
            ),
            {"bs": brand_slug, "ms": model_slug},
        ).mappings().first()
        if row is None:
            print(f"  MISSING model {brand_slug}/{model_slug}")
            continue
        print(
            f"  {brand_slug}/{model_slug} id={row['model_id']} "
            f"active={row['active_refs']} draft={row['draft_refs']} "
            f"total={row['total_refs']} → keep historical refs; "
            f"vehicle_execution left NULL (no guess)"
        )
    print("=== end live ref report ===")


def upgrade() -> None:
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE vehicle_execution_enum AS ENUM ('cargo', 'passenger');
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
        """
    )
    execution_enum = postgresql.ENUM(
        "cargo",
        "passenger",
        name="vehicle_execution_enum",
        create_type=False,
    )

    conn = op.get_bind()
    exists = conn.execute(
        sa.text(
            """
            SELECT 1 FROM information_schema.tables
            WHERE table_name = 'vehicle_model_allowed_executions'
            """
        )
    ).scalar()
    if not exists:
        op.create_table(
            "vehicle_model_allowed_executions",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column(
                "model_id",
                sa.Integer(),
                sa.ForeignKey("vehicle_models.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("execution", execution_enum, nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.UniqueConstraint(
                "model_id",
                "execution",
                name="uq_vehicle_model_allowed_executions_model_exec",
            ),
        )
        op.create_index(
            "ix_vehicle_model_allowed_executions_model_id",
            "vehicle_model_allowed_executions",
            ["model_id"],
        )
        op.create_index(
            "ix_vehicle_model_allowed_executions_execution",
            "vehicle_model_allowed_executions",
            ["execution"],
        )

    col_exists = conn.execute(
        sa.text(
            """
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'listings' AND column_name = 'vehicle_execution'
            """
        )
    ).scalar()
    if not col_exists:
        op.add_column(
            "listings",
            sa.Column("vehicle_execution", execution_enum, nullable=True),
        )
        op.create_index(
            "ix_listings_vehicle_execution",
            "listings",
            ["vehicle_execution"],
        )

    _report_live_refs(conn)

    for brand_slug, model_slug, executions in _SEED:
        mid = conn.execute(
            sa.text(
                """
                SELECT m.id
                FROM vehicle_models m
                JOIN vehicle_brands b ON b.id = m.brand_id
                WHERE b.slug = :bs AND m.slug = :ms
                  AND b.is_enabled IS TRUE AND m.is_enabled IS TRUE
                LIMIT 1
                """
            ),
            {"bs": brand_slug, "ms": model_slug},
        ).scalar()
        if mid is None:
            print(f"SEED SKIP missing {brand_slug}/{model_slug}")
            continue
        for ex in executions:
            conn.execute(
                sa.text(
                    """
                    INSERT INTO vehicle_model_allowed_executions (model_id, execution)
                    VALUES (:mid, CAST(:ex AS vehicle_execution_enum))
                    ON CONFLICT (model_id, execution) DO NOTHING
                    """
                ),
                {"mid": mid, "ex": ex},
            )


def downgrade() -> None:
    op.drop_index("ix_listings_vehicle_execution", table_name="listings")
    op.drop_column("listings", "vehicle_execution")
    op.drop_index(
        "ix_vehicle_model_allowed_executions_execution",
        table_name="vehicle_model_allowed_executions",
    )
    op.drop_index(
        "ix_vehicle_model_allowed_executions_model_id",
        table_name="vehicle_model_allowed_executions",
    )
    op.drop_table("vehicle_model_allowed_executions")
    op.execute("DROP TYPE IF EXISTS vehicle_execution_enum")
