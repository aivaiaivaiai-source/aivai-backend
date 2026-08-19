"""listing promotion window + wallet ledger

Revision ID: f1c8e44b9d02
Revises: e4b9d21c7a55
Create Date: 2026-08-18 17:10:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f1c8e44b9d02"
down_revision: Union[str, None] = "e4b9d21c7a55"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("listings", sa.Column("promotion_daily_rate", sa.Integer(), nullable=True))
    op.add_column(
        "listings",
        sa.Column("promotion_tier", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "listings",
        sa.Column("promotion_starts_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "listings",
        sa.Column("promotion_ends_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_listings_promotion_tier", "listings", ["promotion_tier"])
    op.create_index("ix_listings_promotion_ends_at", "listings", ["promotion_ends_at"])
    op.execute(
        """
        UPDATE listings
        SET promotion_starts_at = now(),
            promotion_ends_at = now() + interval '30 days',
            promotion_tier = 1,
            promotion_daily_rate = 70
        WHERE is_promoted IS TRUE
          AND promotion_ends_at IS NULL
        """
    )

    wallet_kind = sa.Enum(
        "promotion_charge",
        "topup",
        "refund",
        name="wallet_ledger_kind_enum",
    )
    op.create_table(
        "wallet_ledger",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("delta", sa.Numeric(14, 2), nullable=False),
        sa.Column("balance_after", sa.Numeric(14, 2), nullable=False),
        sa.Column("kind", wallet_kind, nullable=False),
        sa.Column("reference_type", sa.String(length=32), nullable=True),
        sa.Column("reference_id", sa.String(length=64), nullable=True),
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
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_wallet_ledger_user_id", "wallet_ledger", ["user_id"])
    op.create_index("ix_wallet_ledger_kind", "wallet_ledger", ["kind"])

    promo_status = sa.Enum(
        "active",
        "stopped",
        "expired",
        name="promotion_order_status_enum",
    )
    op.create_table(
        "promotion_orders",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("listing_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("daily_rate", sa.Integer(), nullable=False),
        sa.Column("days", sa.Integer(), nullable=False),
        sa.Column("discount_percent", sa.Integer(), nullable=False),
        sa.Column("total_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("tier", sa.Integer(), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", promo_status, nullable=False),
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
        sa.ForeignKeyConstraint(["listing_id"], ["listings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_promotion_orders_listing_id", "promotion_orders", ["listing_id"])
    op.create_index("ix_promotion_orders_user_id", "promotion_orders", ["user_id"])
    op.create_index("ix_promotion_orders_ends_at", "promotion_orders", ["ends_at"])
    op.create_index("ix_promotion_orders_status", "promotion_orders", ["status"])


def downgrade() -> None:
    op.drop_index("ix_promotion_orders_status", table_name="promotion_orders")
    op.drop_index("ix_promotion_orders_ends_at", table_name="promotion_orders")
    op.drop_index("ix_promotion_orders_user_id", table_name="promotion_orders")
    op.drop_index("ix_promotion_orders_listing_id", table_name="promotion_orders")
    op.drop_table("promotion_orders")
    sa.Enum(name="promotion_order_status_enum").drop(op.get_bind(), checkfirst=True)

    op.drop_index("ix_wallet_ledger_kind", table_name="wallet_ledger")
    op.drop_index("ix_wallet_ledger_user_id", table_name="wallet_ledger")
    op.drop_table("wallet_ledger")
    sa.Enum(name="wallet_ledger_kind_enum").drop(op.get_bind(), checkfirst=True)

    op.drop_index("ix_listings_promotion_ends_at", table_name="listings")
    op.drop_index("ix_listings_promotion_tier", table_name="listings")
    op.drop_column("listings", "promotion_ends_at")
    op.drop_column("listings", "promotion_starts_at")
    op.drop_column("listings", "promotion_tier")
    op.drop_column("listings", "promotion_daily_rate")
