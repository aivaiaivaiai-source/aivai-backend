"""Currency Policy V2: FX rate table + listing snapshot/normalized columns.

Revision ID: n4i5j6k7l8m9currencyv2
Revises: m3h4i5j6k7l8tireswheelsv2
Create Date: 2026-11-03
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "n4i5j6k7l8m9currencyv2"
down_revision = "m3h4i5j6k7l8tireswheelsv2"
branch_labels = None
depends_on = None

# Configured migration/dev fallback — not a live market claim.
_MIGRATION_RATE = "89"


def upgrade() -> None:
    op.create_table(
        "fx_rates",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("pair", sa.String(length=16), nullable=False),
        sa.Column("rate", sa.Numeric(18, 6), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False, server_default="configured"),
        sa.Column(
            "rate_updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("pair", name="uq_fx_rates_pair"),
    )
    op.create_index("ix_fx_rates_pair", "fx_rates", ["pair"])

    op.add_column(
        "listings",
        sa.Column("exchange_rate_snapshot", sa.Numeric(18, 6), nullable=True),
    )
    op.add_column(
        "listings",
        sa.Column("normalized_price_kgs", sa.Numeric(14, 2), nullable=True),
    )
    op.create_index(
        "ix_listings_normalized_price_kgs",
        "listings",
        ["normalized_price_kgs"],
    )

    # Seed configured FX row (dev/migration fallback — not a live market claim).
    op.execute(
        f"""
        INSERT INTO fx_rates (pair, rate, source, rate_updated_at, created_at, updated_at)
        VALUES ('USD_KGS', {_MIGRATION_RATE}, 'configured', now(), now(), now())
        ON CONFLICT (pair) DO NOTHING
        """
    )

    # Backfill existing listings (all historically KGS after old publish conversion).
    # Do NOT attempt to reconstruct lost original USD amounts.
    op.execute(
        f"""
        UPDATE listings
        SET exchange_rate_snapshot = {_MIGRATION_RATE},
            normalized_price_kgs = CASE
              WHEN currency::text = 'USD'
                THEN ROUND((price * {_MIGRATION_RATE})::numeric, 2)
              ELSE ROUND(price::numeric, 2)
            END
        WHERE normalized_price_kgs IS NULL
        """
    )


def downgrade() -> None:
    op.drop_index("ix_listings_normalized_price_kgs", table_name="listings")
    op.drop_column("listings", "normalized_price_kgs")
    op.drop_column("listings", "exchange_rate_snapshot")
    op.drop_index("ix_fx_rates_pair", table_name="fx_rates")
    op.drop_table("fx_rates")
