"""listings feed composite indexes

Revision ID: f7a2b34c8d01
Revises: e6a1c34d8f03
Create Date: 2026-08-12

"""

from typing import Sequence, Union

from alembic import op

revision: str = "f7a2b34c8d01"
down_revision: Union[str, None] = "e6a1c34d8f03"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_listings_status_created_at",
        "listings",
        ["status", "created_at"],
        unique=False,
        postgresql_ops={"created_at": "DESC"},
    )
    op.create_index(
        "ix_listings_status_category_id_created_at",
        "listings",
        ["status", "category_id", "created_at"],
        unique=False,
        postgresql_ops={"created_at": "DESC"},
    )


def downgrade() -> None:
    op.drop_index(
        "ix_listings_status_category_id_created_at",
        table_name="listings",
    )
    op.drop_index(
        "ix_listings_status_created_at",
        table_name="listings",
    )
