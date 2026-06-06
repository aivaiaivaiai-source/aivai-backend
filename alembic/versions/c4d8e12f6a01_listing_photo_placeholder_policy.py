"""listing photo placeholder policy columns

Revision ID: c4d8e12f6a01
Revises: b5e2f8a91c03
Create Date: 2026-05-21

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c4d8e12f6a01"
down_revision: Union[str, None] = "b5e2f8a91c03"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "listings",
        sa.Column("uses_placeholder_image", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "media",
        sa.Column("is_placeholder", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("media", "is_placeholder")
    op.drop_column("listings", "uses_placeholder_image")
