"""Categorize foods for catalog navigation.

Revision ID: 0004_add_food_categories
Revises: 0003_create_recipes
Create Date: 2026-09-04
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_add_food_categories"
down_revision: str | Sequence[str] | None = "0003_create_recipes"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "foods",
        sa.Column(
            "category",
            sa.String(length=20),
            server_default="other",
            nullable=False,
        ),
    )
    op.create_check_constraint(
        "ck_foods_category",
        "foods",
        "category IN ('protein', 'carbohydrate', 'vegetable', 'dairy', "
        "'fat', 'sauce', 'spice', 'other')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_foods_category", "foods", type_="check")
    op.drop_column("foods", "category")
