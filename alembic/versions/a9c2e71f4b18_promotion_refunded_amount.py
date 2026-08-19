"""promotion order refunded_amount

Revision ID: a9c2e71f4b18
Revises: f1c8e44b9d02
Create Date: 2026-08-18 20:04:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a9c2e71f4b18"
down_revision: Union[str, None] = "f1c8e44b9d02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "promotion_orders",
        sa.Column(
            "refunded_amount",
            sa.Numeric(14, 2),
            nullable=False,
            server_default="0",
        ),
    )


def downgrade() -> None:
    op.drop_column("promotion_orders", "refunded_amount")
