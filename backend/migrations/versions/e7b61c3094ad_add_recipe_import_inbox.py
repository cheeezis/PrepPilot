"""add recipe import inbox

Revision ID: e7b61c3094ad
Revises: c3d7e6a421bf
Create Date: 2026-08-29

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e7b61c3094ad"
down_revision: str | Sequence[str] | None = "c3d7e6a421bf"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "recipe_imports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_name", sa.String(length=100), nullable=False),
        sa.Column("external_id", sa.String(length=200), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("raw_payload", sa.JSON(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("raw_servings", sa.String(length=100), nullable=True),
        sa.Column("manual_servings", sa.Numeric(10, 3), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "received",
                "ready_for_catalog_review",
                "needs_review",
                "rejected",
                name="recipe_import_status",
            ),
            nullable=False,
        ),
        sa.CheckConstraint(
            "length(trim(source_name)) > 0",
            name="ck_recipe_imports_source_name_not_blank",
        ),
        sa.CheckConstraint(
            "length(trim(external_id)) > 0",
            name="ck_recipe_imports_external_id_not_blank",
        ),
        sa.CheckConstraint(
            "length(content_hash) = 64",
            name="ck_recipe_imports_content_hash_sha256",
        ),
        sa.CheckConstraint(
            "manual_servings IS NULL OR manual_servings > 0",
            name="ck_recipe_imports_manual_servings_positive",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source_name",
            "external_id",
            "content_hash",
            name="uq_recipe_imports_source_external_content",
        ),
    )
    op.create_table(
        "food_aliases",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("alias", sa.String(length=300), nullable=False),
        sa.Column("normalized_alias", sa.String(length=300), nullable=False),
        sa.Column("food_id", sa.Integer(), nullable=False),
        sa.Column("source_name", sa.String(length=100), nullable=True),
        sa.CheckConstraint(
            "length(trim(alias)) > 0", name="ck_food_aliases_alias_not_blank"
        ),
        sa.CheckConstraint(
            "length(trim(normalized_alias)) > 0",
            name="ck_food_aliases_normalized_alias_not_blank",
        ),
        sa.ForeignKeyConstraint(["food_id"], ["foods.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "normalized_alias", name="uq_food_aliases_normalized_alias"
        ),
    )
    op.create_table(
        "food_measure_defaults",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("food_id", sa.Integer(), nullable=False),
        sa.Column("measure_key", sa.String(length=100), nullable=False),
        sa.Column("amount", sa.Numeric(12, 3), nullable=False),
        sa.Column("source_name", sa.String(length=200), nullable=False),
        sa.Column("source_reference", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "length(trim(measure_key)) > 0",
            name="ck_food_measure_defaults_key_not_blank",
        ),
        sa.CheckConstraint(
            "amount > 0", name="ck_food_measure_defaults_amount_positive"
        ),
        sa.CheckConstraint(
            "length(trim(source_name)) > 0",
            name="ck_food_measure_defaults_source_not_blank",
        ),
        sa.ForeignKeyConstraint(["food_id"], ["foods.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "food_id",
            "measure_key",
            name="uq_food_measure_defaults_food_measure",
        ),
    )
    op.create_table(
        "recipe_import_ingredients",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("recipe_import_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("raw_line", sa.Text(), nullable=False),
        sa.Column("raw_name", sa.String(length=300), nullable=False),
        sa.Column("raw_amount", sa.String(length=100), nullable=True),
        sa.Column("raw_unit", sa.String(length=100), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "normalized",
                "needs_review",
                "excluded",
                name="imported_ingredient_status",
            ),
            nullable=False,
        ),
        sa.Column(
            "review_reason",
            sa.Enum(
                "unknown_food",
                "ambiguous_food",
                "unsupported_unit",
                "missing_measure_default",
                "invalid_or_ranged_quantity",
                "incompatible_measurement",
                "missing_serving_count",
                name="import_review_reason",
            ),
            nullable=True,
        ),
        sa.Column("food_id", sa.Integer(), nullable=True),
        sa.Column("manual_food_id", sa.Integer(), nullable=True),
        sa.Column("normalized_amount", sa.Numeric(12, 3), nullable=True),
        sa.Column("manual_amount", sa.Numeric(12, 3), nullable=True),
        sa.Column("excluded", sa.Boolean(), nullable=False),
        sa.CheckConstraint("position >= 0", name="ck_import_ingredients_position"),
        sa.CheckConstraint(
            "length(trim(raw_line)) > 0",
            name="ck_import_ingredients_raw_line_not_blank",
        ),
        sa.CheckConstraint(
            "length(trim(raw_name)) > 0",
            name="ck_import_ingredients_raw_name_not_blank",
        ),
        sa.CheckConstraint(
            "manual_amount IS NULL OR manual_amount > 0",
            name="ck_import_ingredients_manual_amount_positive",
        ),
        sa.CheckConstraint(
            "normalized_amount IS NULL OR normalized_amount > 0",
            name="ck_import_ingredients_normalized_amount_positive",
        ),
        sa.ForeignKeyConstraint(["food_id"], ["foods.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["manual_food_id"], ["foods.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["recipe_import_id"], ["recipe_imports.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "recipe_import_id",
            "position",
            name="uq_import_ingredients_recipe_position",
        ),
    )
    op.create_table(
        "import_review_decisions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("recipe_import_id", sa.Integer(), nullable=False),
        sa.Column("ingredient_id", sa.Integer(), nullable=True),
        sa.Column(
            "action",
            sa.Enum(
                "assign_food",
                "add_alias",
                "add_measure_default",
                "override_amount",
                "exclude",
                "set_servings",
                "reject",
                name="review_decision_action",
            ),
            nullable=False,
        ),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["ingredient_id"],
            ["recipe_import_ingredients.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["recipe_import_id"], ["recipe_imports.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("import_review_decisions")
    op.drop_table("recipe_import_ingredients")
    op.drop_table("food_measure_defaults")
    op.drop_table("food_aliases")
    op.drop_table("recipe_imports")
    bind = op.get_bind()
    for enum_name in (
        "review_decision_action",
        "import_review_reason",
        "imported_ingredient_status",
        "recipe_import_status",
    ):
        sa.Enum(name=enum_name).drop(bind, checkfirst=True)
