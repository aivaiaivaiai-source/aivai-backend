"""category intelligence arch review indexes and locale

Revision ID: b5e2f8a91c03
Revises: a3b8c91d4e02
Create Date: 2026-05-21 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "b5e2f8a91c03"
down_revision: Union[str, Sequence[str], None] = "a3b8c91d4e02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- category_aliases ---
    op.add_column(
        "category_aliases",
        sa.Column("alias_compact", sa.String(length=160), nullable=False, server_default=""),
    )
    op.add_column(
        "category_aliases",
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.drop_constraint("uq_category_aliases_normalized", "category_aliases", type_="unique")
    op.create_unique_constraint(
        "uq_category_aliases_normalized_locale",
        "category_aliases",
        ["alias_normalized", "locale"],
    )
    op.create_index(
        "ix_category_aliases_compact_locale",
        "category_aliases",
        ["alias_compact", "locale"],
        unique=False,
    )
    op.create_index(
        "ix_category_aliases_category_enabled",
        "category_aliases",
        ["category_id", "is_enabled"],
        unique=False,
    )
    op.alter_column("category_aliases", "alias_compact", server_default=None)
    op.execute(
        "UPDATE category_aliases SET alias_compact = regexp_replace(lower(alias_normalized), '[^a-z0-9]', '', 'g') "
        "WHERE alias_compact = '' OR alias_compact IS NULL"
    )

    # --- vehicle ---
    op.add_column(
        "vehicle_brands",
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.add_column(
        "vehicle_models",
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.add_column(
        "vehicle_aliases",
        sa.Column("alias_compact", sa.String(length=120), nullable=False, server_default=""),
    )
    op.add_column(
        "vehicle_aliases",
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.drop_constraint("uq_vehicle_aliases_normalized", "vehicle_aliases", type_="unique")
    op.create_unique_constraint(
        "uq_vehicle_aliases_compact_locale",
        "vehicle_aliases",
        ["alias_compact", "locale"],
    )
    op.create_index(
        "ix_vehicle_aliases_normalized_locale",
        "vehicle_aliases",
        ["alias_normalized", "locale"],
        unique=False,
    )
    op.create_index(
        "ix_vehicle_aliases_enabled",
        "vehicle_aliases",
        ["is_enabled"],
        unique=False,
    )
    op.create_index(
        "ix_vehicle_models_brand_slug",
        "vehicle_models",
        ["brand_id", "slug"],
        unique=False,
    )
    op.alter_column("vehicle_aliases", "alias_compact", server_default=None)
    op.execute(
        "UPDATE vehicle_aliases SET alias_compact = regexp_replace(lower(alias_normalized), '[^a-z0-9]', '', 'g') "
        "WHERE alias_compact = '' OR alias_compact IS NULL"
    )

    # --- categories composite ---
    op.create_index(
        "ix_categories_parent_active_sort",
        "categories",
        ["parent_id", "is_active", "sort_order"],
        unique=False,
    )
    op.create_index(op.f("ix_categories_is_active"), "categories", ["is_active"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_categories_is_active"), table_name="categories")
    op.drop_index("ix_categories_parent_active_sort", table_name="categories")

    op.drop_index("ix_vehicle_models_brand_slug", table_name="vehicle_models")
    op.drop_index("ix_vehicle_aliases_enabled", table_name="vehicle_aliases")
    op.drop_index("ix_vehicle_aliases_normalized_locale", table_name="vehicle_aliases")
    op.drop_constraint("uq_vehicle_aliases_compact_locale", "vehicle_aliases", type_="unique")
    op.create_unique_constraint(
        "uq_vehicle_aliases_normalized",
        "vehicle_aliases",
        ["alias_normalized"],
    )
    op.drop_column("vehicle_aliases", "is_enabled")
    op.drop_column("vehicle_aliases", "alias_compact")
    op.drop_column("vehicle_models", "is_enabled")
    op.drop_column("vehicle_brands", "is_enabled")

    op.drop_index("ix_category_aliases_category_enabled", table_name="category_aliases")
    op.drop_index("ix_category_aliases_compact_locale", table_name="category_aliases")
    op.drop_constraint("uq_category_aliases_normalized_locale", "category_aliases", type_="unique")
    op.create_unique_constraint(
        "uq_category_aliases_normalized",
        "category_aliases",
        ["alias_normalized"],
    )
    op.drop_column("category_aliases", "is_enabled")
    op.drop_column("category_aliases", "alias_compact")
