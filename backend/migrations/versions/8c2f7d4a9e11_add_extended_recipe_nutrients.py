"""add extended recipe nutrients

Revision ID: 8c2f7d4a9e11
Revises: 6a4d8f2c1b30
Create Date: 2026-09-03
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "8c2f7d4a9e11"
down_revision: str | None = "6a4d8f2c1b30"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

NUTRIENT_COLUMNS = (
    "sugar_per_serving",
    "saturated_fat_per_serving",
    "fiber_per_serving",
    "salt_per_serving",
)


def upgrade() -> None:
    for column_name in NUTRIENT_COLUMNS:
        op.add_column(
            "recipes",
            sa.Column(
                column_name,
                sa.Numeric(10, 2),
                nullable=False,
                server_default="0",
            ),
        )
        op.create_check_constraint(
            f"ck_recipes_{column_name.removesuffix('_per_serving')}_nonnegative",
            "recipes",
            f"{column_name} >= 0",
        )
        op.alter_column("recipes", column_name, server_default=None)


def downgrade() -> None:
    for column_name in reversed(NUTRIENT_COLUMNS):
        op.drop_constraint(
            f"ck_recipes_{column_name.removesuffix('_per_serving')}_nonnegative",
            "recipes",
            type_="check",
        )
        op.drop_column("recipes", column_name)
