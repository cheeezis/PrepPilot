"""Create recipes with roles and food-backed ingredients.

Revision ID: 0003_create_recipes
Revises: 0002_create_foods
Create Date: 2026-09-04
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_create_recipes"
down_revision: str | Sequence[str] | None = "0002_create_foods"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "recipes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("servings", sa.Integer(), nullable=False),
        sa.Column("instructions", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "length(trim(title)) > 0", name="ck_recipes_title_not_blank"
        ),
        sa.CheckConstraint("servings > 0", name="ck_recipes_servings_positive"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "recipe_meal_roles",
        sa.Column("recipe_id", sa.Integer(), nullable=False),
        sa.Column("meal_role", sa.String(length=10), nullable=False),
        sa.CheckConstraint(
            "meal_role IN ('breakfast', 'lunch', 'dinner', 'snack')",
            name="ck_recipe_meal_roles_value",
        ),
        sa.ForeignKeyConstraint(["recipe_id"], ["recipes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("recipe_id", "meal_role"),
    )
    op.create_table(
        "recipe_ingredients",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("recipe_id", sa.Integer(), nullable=False),
        sa.Column("food_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(12, 3), nullable=False),
        sa.Column("unit", sa.String(length=2), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "amount > 0", name="ck_recipe_ingredients_amount_positive"
        ),
        sa.CheckConstraint(
            "unit IN ('g', 'ml')", name="ck_recipe_ingredients_unit"
        ),
        sa.CheckConstraint(
            "position >= 0", name="ck_recipe_ingredients_position_nonnegative"
        ),
        sa.ForeignKeyConstraint(["food_id"], ["foods.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["recipe_id"], ["recipes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "recipe_id", "position", name="uq_recipe_ingredients_position"
        ),
    )
    op.create_index(
        op.f("ix_recipe_ingredients_food_id"),
        "recipe_ingredients",
        ["food_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_recipe_ingredients_recipe_id"),
        "recipe_ingredients",
        ["recipe_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_recipe_ingredients_recipe_id"), table_name="recipe_ingredients"
    )
    op.drop_index(
        op.f("ix_recipe_ingredients_food_id"), table_name="recipe_ingredients"
    )
    op.drop_table("recipe_ingredients")
    op.drop_table("recipe_meal_roles")
    op.drop_table("recipes")
