"""listing is_promoted flag for urgent feed badge

Revision ID: e4b9d21c7a55
Revises: d3e7c18b9a44
Create Date: 2026-08-18 16:20:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e4b9d21c7a55"
down_revision: Union[str, None] = "d3e7c18b9a44"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "listings",
        sa.Column(
            "is_promoted",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )


def downgrade() -> None:
    op.drop_column("listings", "is_promoted")
