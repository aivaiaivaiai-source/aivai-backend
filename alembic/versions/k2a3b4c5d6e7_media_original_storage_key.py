"""media original_storage_key (Stage 2/7)

Revision ID: k2a3b4c5d6e7
Revises: j1f2a3b4c5d6
Create Date: 2026-08-23
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "k2a3b4c5d6e7"
down_revision: Union[str, None] = "j1f2a3b4c5d6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "media",
        sa.Column("original_storage_key", sa.String(length=512), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("media", "original_storage_key")
