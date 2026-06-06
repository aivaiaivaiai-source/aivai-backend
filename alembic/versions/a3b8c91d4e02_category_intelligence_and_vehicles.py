"""category intelligence and vehicle dictionaries

Revision ID: a3b8c91d4e02
Revises: f4819c2eab01
Create Date: 2026-05-21 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "a3b8c91d4e02"
down_revision: Union[str, Sequence[str], None] = "f4819c2eab01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    category_entity_type_enum = postgresql.ENUM(
        "object", "service", "construction", "equipment", "raw_material",
        "business", "food", "animal", "job", "general",
        name="category_entity_type_enum",
        create_type=False,
    )
    category_field_type_enum = postgresql.ENUM(
        "string", "number", "decimal", "boolean", "enum", "city",
        "brand", "model", "year", "price",
        name="category_field_type_enum",
        create_type=False,
    )
    category_filter_type_enum = postgresql.ENUM(
        "range", "select", "multi_select", "boolean", "text",
        name="category_filter_type_enum",
        create_type=False,
    )
    category_rule_type_enum = postgresql.ENUM(
        "routing", "moderation", "guardrail", "dialogue",
        name="category_rule_type_enum",
        create_type=False,
    )
    moderation_action_enum = postgresql.ENUM(
        "allow", "block", "moderation_queue", "warn",
        name="moderation_action_enum",
        create_type=False,
    )
    vehicle_type_enum = postgresql.ENUM(
        "car", "truck", "motorcycle", "special", "bus",
        name="vehicle_type_enum",
        create_type=False,
    )
    vehicle_alias_target_enum = postgresql.ENUM(
        "brand", "model",
        name="vehicle_alias_target_enum",
        create_type=False,
    )

    for enum_type in (
        category_entity_type_enum,
        category_field_type_enum,
        category_filter_type_enum,
        category_rule_type_enum,
        moderation_action_enum,
        vehicle_type_enum,
        vehicle_alias_target_enum,
    ):
        enum_type.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "categories",
        sa.Column(
            "entity_type",
            category_entity_type_enum,
            nullable=False,
            server_default="general",
        ),
    )
    op.add_column("categories", sa.Column("description", sa.Text(), nullable=True))
    op.add_column(
        "categories",
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "categories",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.add_column(
        "categories",
        sa.Column("requires_city", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.add_column("categories", sa.Column("ai_dialogue_hint", sa.Text(), nullable=True))
    op.create_index(op.f("ix_categories_entity_type"), "categories", ["entity_type"], unique=False)
    op.create_index(op.f("ix_categories_sort_order"), "categories", ["sort_order"], unique=False)

    op.create_table(
        "category_aliases",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("alias", sa.String(length=160), nullable=False),
        sa.Column("alias_normalized", sa.String(length=160), nullable=False),
        sa.Column("locale", sa.String(length=8), nullable=False),
        sa.Column("weight", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("alias_normalized", name="uq_category_aliases_normalized"),
    )
    op.create_index(op.f("ix_category_aliases_category_id"), "category_aliases", ["category_id"], unique=False)
    op.create_index(op.f("ix_category_aliases_created_at"), "category_aliases", ["created_at"], unique=False)
    op.create_index(op.f("ix_category_aliases_alias_normalized"), "category_aliases", ["alias_normalized"], unique=False)

    op.create_table(
        "category_core_fields",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("field_key", sa.String(length=64), nullable=False),
        sa.Column("label", sa.String(length=120), nullable=False),
        sa.Column("field_type", category_field_type_enum, nullable=False),
        sa.Column("is_required", sa.Boolean(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("options", sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"), nullable=True),
        sa.Column("ai_hint", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("category_id", "field_key", name="uq_category_core_fields_key"),
    )
    op.create_index(op.f("ix_category_core_fields_category_id"), "category_core_fields", ["category_id"], unique=False)
    op.create_index(op.f("ix_category_core_fields_created_at"), "category_core_fields", ["created_at"], unique=False)

    op.create_table(
        "category_optional_fields",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("field_key", sa.String(length=64), nullable=False),
        sa.Column("label", sa.String(length=120), nullable=False),
        sa.Column("field_type", category_field_type_enum, nullable=False),
        sa.Column("is_required", sa.Boolean(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("options", sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"), nullable=True),
        sa.Column("ai_hint", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("category_id", "field_key", name="uq_category_optional_fields_key"),
    )
    op.create_index(op.f("ix_category_optional_fields_category_id"), "category_optional_fields", ["category_id"], unique=False)
    op.create_index(op.f("ix_category_optional_fields_created_at"), "category_optional_fields", ["created_at"], unique=False)

    op.create_table(
        "category_filters",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("filter_key", sa.String(length=64), nullable=False),
        sa.Column("label", sa.String(length=120), nullable=False),
        sa.Column("filter_type", category_filter_type_enum, nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("config", sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("category_id", "filter_key", name="uq_category_filters_key"),
    )
    op.create_index(op.f("ix_category_filters_category_id"), "category_filters", ["category_id"], unique=False)
    op.create_index(op.f("ix_category_filters_created_at"), "category_filters", ["created_at"], unique=False)

    op.create_table(
        "category_ai_rules",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.Column("rule_type", category_rule_type_enum, nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("pattern", sa.Text(), nullable=True),
        sa.Column("action", moderation_action_enum, nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("config", sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_category_ai_rules_category_id"), "category_ai_rules", ["category_id"], unique=False)
    op.create_index(op.f("ix_category_ai_rules_created_at"), "category_ai_rules", ["created_at"], unique=False)
    op.create_index(op.f("ix_category_ai_rules_rule_type"), "category_ai_rules", ["rule_type"], unique=False)

    op.create_table(
        "vehicle_brands",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("slug", sa.String(length=160), nullable=False),
        sa.Column("country_origin", sa.String(length=64), nullable=True),
        sa.Column("vehicle_type", vehicle_type_enum, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug", name="uq_vehicle_brands_slug"),
    )
    op.create_index(op.f("ix_vehicle_brands_created_at"), "vehicle_brands", ["created_at"], unique=False)
    op.create_index(op.f("ix_vehicle_brands_slug"), "vehicle_brands", ["slug"], unique=False)
    op.create_index(op.f("ix_vehicle_brands_vehicle_type"), "vehicle_brands", ["vehicle_type"], unique=False)

    op.create_table(
        "vehicle_models",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("brand_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("slug", sa.String(length=160), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["brand_id"], ["vehicle_brands.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("brand_id", "slug", name="uq_vehicle_models_brand_slug"),
    )
    op.create_index(op.f("ix_vehicle_models_brand_id"), "vehicle_models", ["brand_id"], unique=False)
    op.create_index(op.f("ix_vehicle_models_created_at"), "vehicle_models", ["created_at"], unique=False)

    op.create_table(
        "vehicle_aliases",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("alias", sa.String(length=120), nullable=False),
        sa.Column("alias_normalized", sa.String(length=120), nullable=False),
        sa.Column("target_type", vehicle_alias_target_enum, nullable=False),
        sa.Column("brand_id", sa.Integer(), nullable=True),
        sa.Column("model_id", sa.Integer(), nullable=True),
        sa.Column("locale", sa.String(length=8), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["brand_id"], ["vehicle_brands.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["model_id"], ["vehicle_models.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("alias_normalized", name="uq_vehicle_aliases_normalized"),
    )
    op.create_index(op.f("ix_vehicle_aliases_alias_normalized"), "vehicle_aliases", ["alias_normalized"], unique=False)
    op.create_index(op.f("ix_vehicle_aliases_brand_id"), "vehicle_aliases", ["brand_id"], unique=False)
    op.create_index(op.f("ix_vehicle_aliases_created_at"), "vehicle_aliases", ["created_at"], unique=False)
    op.create_index(op.f("ix_vehicle_aliases_model_id"), "vehicle_aliases", ["model_id"], unique=False)


def downgrade() -> None:
    op.drop_table("vehicle_aliases")
    op.drop_table("vehicle_models")
    op.drop_table("vehicle_brands")
    op.drop_table("category_ai_rules")
    op.drop_table("category_filters")
    op.drop_table("category_optional_fields")
    op.drop_table("category_core_fields")
    op.drop_table("category_aliases")

    op.drop_index(op.f("ix_categories_sort_order"), table_name="categories")
    op.drop_index(op.f("ix_categories_entity_type"), table_name="categories")
    op.drop_column("categories", "ai_dialogue_hint")
    op.drop_column("categories", "requires_city")
    op.drop_column("categories", "is_active")
    op.drop_column("categories", "sort_order")
    op.drop_column("categories", "description")
    op.drop_column("categories", "entity_type")

    vehicle_alias_target_enum = postgresql.ENUM(name="vehicle_alias_target_enum", create_type=False)
    vehicle_type_enum = postgresql.ENUM(name="vehicle_type_enum", create_type=False)
    moderation_action_enum = postgresql.ENUM(name="moderation_action_enum", create_type=False)
    category_rule_type_enum = postgresql.ENUM(name="category_rule_type_enum", create_type=False)
    category_filter_type_enum = postgresql.ENUM(name="category_filter_type_enum", create_type=False)
    category_field_type_enum = postgresql.ENUM(name="category_field_type_enum", create_type=False)
    category_entity_type_enum = postgresql.ENUM(name="category_entity_type_enum", create_type=False)

    for enum_type in (
        vehicle_alias_target_enum,
        vehicle_type_enum,
        moderation_action_enum,
        category_rule_type_enum,
        category_filter_type_enum,
        category_field_type_enum,
        category_entity_type_enum,
    ):
        enum_type.drop(op.get_bind(), checkfirst=True)
