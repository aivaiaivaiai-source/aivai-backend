"""listing field values storage

Revision ID: a1c9e3f82b04
Revises: f7a2b34c8d01
Create Date: 2026-08-12

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a1c9e3f82b04"
down_revision: Union[str, None] = "f7a2b34c8d01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_SINGLE_VALUE_CHECK = """
(
    (value_text IS NOT NULL)::int +
    (value_int IS NOT NULL)::int +
    (value_decimal IS NOT NULL)::int +
    (value_bool IS NOT NULL)::int +
    (value_date IS NOT NULL)::int +
    (ref_brand_id IS NOT NULL)::int +
    (ref_model_id IS NOT NULL)::int
) = 1
"""


def upgrade() -> None:
    op.create_table(
        "listing_field_values",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("listing_id", sa.Integer(), nullable=False),
        sa.Column("field_key", sa.String(length=64), nullable=False),
        sa.Column("value_text", sa.Text(), nullable=True),
        sa.Column("value_int", sa.Integer(), nullable=True),
        sa.Column("value_decimal", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("value_bool", sa.Boolean(), nullable=True),
        sa.Column("value_date", sa.Date(), nullable=True),
        sa.Column("ref_brand_id", sa.Integer(), nullable=True),
        sa.Column("ref_model_id", sa.Integer(), nullable=True),
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
        sa.ForeignKeyConstraint(["ref_brand_id"], ["vehicle_brands.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["ref_model_id"], ["vehicle_models.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("listing_id", "field_key", name="uq_listing_field_values_listing_key"),
        sa.CheckConstraint(_SINGLE_VALUE_CHECK, name="ck_listing_field_values_single_value"),
    )
    op.create_index(
        op.f("ix_listing_field_values_listing_id"),
        "listing_field_values",
        ["listing_id"],
        unique=False,
    )
    op.create_index(
        "ix_listing_field_values_field_key_value_int",
        "listing_field_values",
        ["field_key", "value_int"],
        unique=False,
    )
    op.create_index(
        "ix_listing_field_values_field_key_value_decimal",
        "listing_field_values",
        ["field_key", "value_decimal"],
        unique=False,
    )
    op.create_index(
        "ix_listing_field_values_field_key_value_text",
        "listing_field_values",
        ["field_key", "value_text"],
        unique=False,
    )
    op.create_index(
        "ix_listing_field_values_field_key_ref_brand_id",
        "listing_field_values",
        ["field_key", "ref_brand_id"],
        unique=False,
    )
    op.create_index(
        "ix_listing_field_values_field_key_ref_model_id",
        "listing_field_values",
        ["field_key", "ref_model_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_listing_field_values_field_key_ref_model_id",
        table_name="listing_field_values",
    )
    op.drop_index(
        "ix_listing_field_values_field_key_ref_brand_id",
        table_name="listing_field_values",
    )
    op.drop_index(
        "ix_listing_field_values_field_key_value_text",
        table_name="listing_field_values",
    )
    op.drop_index(
        "ix_listing_field_values_field_key_value_decimal",
        table_name="listing_field_values",
    )
    op.drop_index(
        "ix_listing_field_values_field_key_value_int",
        table_name="listing_field_values",
    )
    op.drop_index(
        op.f("ix_listing_field_values_listing_id"),
        table_name="listing_field_values",
    )
    op.drop_table("listing_field_values")
