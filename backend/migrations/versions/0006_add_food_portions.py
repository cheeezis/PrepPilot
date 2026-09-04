"""add food portions

Revision ID: 0006_add_food_portions
Revises: 0005_create_weekly_plans
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006_add_food_portions"
down_revision: str | None = "0005_create_weekly_plans"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("ck_foods_category", "foods", type_="check")
    op.create_check_constraint(
        "ck_foods_category",
        "foods",
        "category IN ('protein', 'carbohydrate', 'vegetable', 'fruit', "
        "'dairy', 'fat', 'sauce', 'spice', 'other')",
    )
    op.create_table(
        "food_portions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("food_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("amount", sa.Numeric(12, 3), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "length(trim(name)) > 0", name="ck_food_portions_name_not_blank"
        ),
        sa.CheckConstraint("amount > 0", name="ck_food_portions_amount_positive"),
        sa.CheckConstraint(
            "position >= 0", name="ck_food_portions_position_nonnegative"
        ),
        sa.ForeignKeyConstraint(["food_id"], ["foods.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("food_id", "position", name="uq_food_portions_position"),
    )
    op.create_index("ix_food_portions_food_id", "food_portions", ["food_id"])
    op.create_index(
        "uq_food_portions_food_name_ci",
        "food_portions",
        ["food_id", sa.text("lower(name)")],
        unique=True,
    )
    op.add_column(
        "recipe_ingredients",
        sa.Column("food_portion_id", sa.Integer(), nullable=True),
    )
    op.create_index(
        "ix_recipe_ingredients_food_portion_id",
        "recipe_ingredients",
        ["food_portion_id"],
    )
    op.create_foreign_key(
        "fk_recipe_ingredients_food_portion_id",
        "recipe_ingredients",
        "food_portions",
        ["food_portion_id"],
        ["id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_recipe_ingredients_food_portion_id",
        "recipe_ingredients",
        type_="foreignkey",
    )
    op.drop_index(
        "ix_recipe_ingredients_food_portion_id", table_name="recipe_ingredients"
    )
    op.drop_column("recipe_ingredients", "food_portion_id")
    op.drop_index("uq_food_portions_food_name_ci", table_name="food_portions")
    op.drop_index("ix_food_portions_food_id", table_name="food_portions")
    op.drop_table("food_portions")
    op.drop_constraint("ck_foods_category", "foods", type_="check")
    op.create_check_constraint(
        "ck_foods_category",
        "foods",
        "category IN ('protein', 'carbohydrate', 'vegetable', 'dairy', "
        "'fat', 'sauce', 'spice', 'other')",
    )
