"""Allow null category_id on draft listings (Media Classification Substage 1).

Revision ID: n6d7e8f9a0b1
Revises: m5c6d7e8f9a0
Create Date: 2026-08-25
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "n6d7e8f9a0b1"
down_revision: Union[str, None] = "m5c6d7e8f9a0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "listings",
        "category_id",
        existing_type=sa.Integer(),
        nullable=True,
    )


def downgrade() -> None:
    # Unsafe if null drafts exist — refuse rather than invent fake categories.
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM listings WHERE category_id IS NULL) THEN
                RAISE EXCEPTION
                    'Cannot downgrade: listings with NULL category_id exist';
            END IF;
        END $$;
        """
    )
    op.alter_column(
        "listings",
        "category_id",
        existing_type=sa.Integer(),
        nullable=False,
    )
