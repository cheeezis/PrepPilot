"""Create persistent weekly plans and meal assignments.

Revision ID: 0005_create_weekly_plans
Revises: 0004_add_food_categories
Create Date: 2026-09-04
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_create_weekly_plans"
down_revision: str | Sequence[str] | None = "0004_add_food_categories"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "weekly_plans",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("snacks_per_day", sa.Integer(), nullable=False),
        sa.Column("calories_target_kcal", sa.Numeric(10, 2), nullable=False),
        sa.Column("protein_minimum_g", sa.Numeric(10, 2), nullable=False),
        sa.Column("carbohydrates_target_g", sa.Numeric(10, 2), nullable=False),
        sa.Column("fat_maximum_g", sa.Numeric(10, 2), nullable=False),
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
            "end_date >= start_date", name="ck_weekly_plans_date_order"
        ),
        sa.CheckConstraint(
            "snacks_per_day BETWEEN 0 AND 3",
            name="ck_weekly_plans_snacks_per_day",
        ),
        sa.CheckConstraint(
            "calories_target_kcal > 0",
            name="ck_weekly_plans_calories_positive",
        ),
        sa.CheckConstraint(
            "protein_minimum_g >= 0",
            name="ck_weekly_plans_protein_nonnegative",
        ),
        sa.CheckConstraint(
            "carbohydrates_target_g >= 0",
            name="ck_weekly_plans_carbohydrates_nonnegative",
        ),
        sa.CheckConstraint(
            "fat_maximum_g >= 0", name="ck_weekly_plans_fat_nonnegative"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "start_date", "end_date", name="uq_weekly_plans_period"
        ),
    )
    op.create_table(
        "meal_assignments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("weekly_plan_id", sa.Integer(), nullable=False),
        sa.Column("day_index", sa.Integer(), nullable=False),
        sa.Column("meal_role", sa.String(length=10), nullable=False),
        sa.Column("slot_number", sa.Integer(), nullable=False),
        sa.Column("recipe_id", sa.Integer(), nullable=False),
        sa.Column("portion_number", sa.Integer(), nullable=True),
        sa.CheckConstraint(
            "day_index BETWEEN 0 AND 6",
            name="ck_meal_assignments_day_index",
        ),
        sa.CheckConstraint(
            "meal_role IN ('breakfast', 'lunch', 'dinner', 'snack')",
            name="ck_meal_assignments_role",
        ),
        sa.CheckConstraint(
            "(meal_role = 'snack' AND slot_number BETWEEN 1 AND 3) OR "
            "(meal_role <> 'snack' AND slot_number = 1)",
            name="ck_meal_assignments_slot_number",
        ),
        sa.CheckConstraint(
            "portion_number IS NULL OR portion_number > 0",
            name="ck_meal_assignments_portion_positive",
        ),
        sa.ForeignKeyConstraint(
            ["recipe_id"], ["recipes.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["weekly_plan_id"], ["weekly_plans.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "weekly_plan_id",
            "day_index",
            "meal_role",
            "slot_number",
            name="uq_meal_assignments_slot",
        ),
        sa.UniqueConstraint(
            "weekly_plan_id",
            "recipe_id",
            "portion_number",
            name="uq_meal_assignments_batch_portion",
        ),
    )
    op.create_index(
        op.f("ix_meal_assignments_recipe_id"),
        "meal_assignments",
        ["recipe_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_meal_assignments_weekly_plan_id"),
        "meal_assignments",
        ["weekly_plan_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_meal_assignments_weekly_plan_id"),
        table_name="meal_assignments",
    )
    op.drop_index(
        op.f("ix_meal_assignments_recipe_id"),
        table_name="meal_assignments",
    )
    op.drop_table("meal_assignments")
    op.drop_table("weekly_plans")
