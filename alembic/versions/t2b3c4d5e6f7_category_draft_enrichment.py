"""Substage 3C-4 — category draft enrichment provenance + feedback."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "t2b3c4d5e6f7"
down_revision = "s1a2b3c4d5e6"
branch_labels = None
depends_on = None

category_selection_source_enum = postgresql.ENUM(
    "manual",
    "resolver",
    name="category_selection_source_enum",
    create_type=False,
)

feedback_outcome_enum = postgresql.ENUM(
    "corrected",
    "accepted_implicitly",
    name="category_resolver_feedback_outcome_enum",
    create_type=False,
)


def upgrade() -> None:
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE category_selection_source_enum AS ENUM ('manual', 'resolver');
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
        """
    )
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE category_resolver_feedback_outcome_enum AS ENUM (
                'corrected', 'accepted_implicitly'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
        """
    )

    bind = op.get_bind()
    insp = sa.inspect(bind)
    listing_cols = {c["name"] for c in insp.get_columns("listings")}
    if "category_selection_source" not in listing_cols:
        op.add_column(
            "listings",
            sa.Column(
                "category_selection_source",
                category_selection_source_enum,
                nullable=True,
            ),
        )

    if not insp.has_table("listing_category_resolver_feedback"):
        op.create_table(
            "listing_category_resolver_feedback",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column(
                "listing_id",
                sa.Integer(),
                sa.ForeignKey("listings.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "resolver_result_id",
                sa.Integer(),
                sa.ForeignKey("listing_category_resolver_results.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column(
                "suggested_category_id",
                sa.Integer(),
                sa.ForeignKey("categories.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column(
                "selected_category_id",
                sa.Integer(),
                sa.ForeignKey("categories.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("outcome", feedback_outcome_enum, nullable=False),
            sa.Column("resolver_version", sa.String(length=64), nullable=True),
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
        )
        op.create_index(
            "ix_listing_category_resolver_feedback_listing_id",
            "listing_category_resolver_feedback",
            ["listing_id"],
        )


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if insp.has_table("listing_category_resolver_feedback"):
        op.drop_index(
            "ix_listing_category_resolver_feedback_listing_id",
            table_name="listing_category_resolver_feedback",
        )
        op.drop_table("listing_category_resolver_feedback")
    listing_cols = {c["name"] for c in insp.get_columns("listings")}
    if "category_selection_source" in listing_cols:
        op.drop_column("listings", "category_selection_source")
    op.execute("DROP TYPE IF EXISTS category_resolver_feedback_outcome_enum")
    op.execute("DROP TYPE IF EXISTS category_selection_source_enum")
