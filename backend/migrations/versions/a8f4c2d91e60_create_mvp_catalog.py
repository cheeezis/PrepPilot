"""create MVP catalog

Revision ID: a8f4c2d91e60
Revises:
Create Date: 2026-08-27

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a8f4c2d91e60"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "foods",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("catalog_key", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("brand", sa.String(length=200), nullable=True),
        sa.Column("unit", sa.Enum("g", "ml", name="measurement_unit"), nullable=False),
        sa.Column(
            "calories_per_100", sa.Numeric(precision=10, scale=4), nullable=False
        ),
        sa.Column("protein_per_100", sa.Numeric(10, 4), nullable=False),
        sa.Column("carbs_per_100", sa.Numeric(10, 4), nullable=False),
        sa.Column("fat_per_100", sa.Numeric(10, 4), nullable=False),
        sa.Column("source_name", sa.String(length=200), nullable=False),
        sa.Column("source_reference", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "length(trim(catalog_key)) > 0", name="ck_foods_catalog_key_not_blank"
        ),
        sa.CheckConstraint("length(trim(name)) > 0", name="ck_foods_name_not_blank"),
        sa.CheckConstraint(
            "length(trim(source_name)) > 0",
            name="ck_foods_source_name_not_blank",
        ),
        sa.CheckConstraint(
            "calories_per_100 >= 0", name="ck_foods_calories_nonnegative"
        ),
        sa.CheckConstraint("protein_per_100 >= 0", name="ck_foods_protein_nonnegative"),
        sa.CheckConstraint("carbs_per_100 >= 0", name="ck_foods_carbs_nonnegative"),
        sa.CheckConstraint("fat_per_100 >= 0", name="ck_foods_fat_nonnegative"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("catalog_key"),
    )
    op.create_table(
        "meals",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("catalog_key", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("preparation_minutes", sa.Integer(), nullable=False),
        sa.Column("instructions", sa.Text(), nullable=False),
        sa.CheckConstraint(
            "length(trim(catalog_key)) > 0", name="ck_meals_catalog_key_not_blank"
        ),
        sa.CheckConstraint("length(trim(name)) > 0", name="ck_meals_name_not_blank"),
        sa.CheckConstraint(
            "preparation_minutes >= 0",
            name="ck_meals_preparation_minutes_nonnegative",
        ),
        sa.CheckConstraint(
            "length(trim(instructions)) > 0",
            name="ck_meals_instructions_not_blank",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("catalog_key"),
    )
    op.create_table(
        "meal_ingredients",
        sa.Column("meal_id", sa.Integer(), nullable=False),
        sa.Column("food_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=3), nullable=False),
        sa.CheckConstraint("amount > 0", name="ck_meal_ingredients_amount_positive"),
        sa.ForeignKeyConstraint(["food_id"], ["foods.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["meal_id"], ["meals.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("meal_id", "food_id"),
    )
    op.create_table(
        "meal_roles",
        sa.Column("meal_id", sa.Integer(), nullable=False),
        sa.Column(
            "role",
            sa.Enum(
                "first_meal",
                "quick_lunch",
                "protein_snack",
                "main_meal",
                "late_snack",
                name="meal_role",
            ),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["meal_id"], ["meals.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("meal_id", "role"),
    )


def downgrade() -> None:
    op.drop_table("meal_roles")
    op.drop_table("meal_ingredients")
    op.drop_table("meals")
    op.drop_table("foods")
    sa.Enum(name="meal_role").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="measurement_unit").drop(op.get_bind(), checkfirst=True)
