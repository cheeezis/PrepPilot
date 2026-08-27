"""add meal portion factors

Revision ID: c3d7e6a421bf
Revises: a8f4c2d91e60
Create Date: 2026-08-27

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c3d7e6a421bf"
down_revision: str | Sequence[str] | None = "a8f4c2d91e60"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "meal_portion_factors",
        sa.Column("meal_id", sa.Integer(), nullable=False),
        sa.Column("factor", sa.Numeric(precision=2, scale=1), nullable=False),
        sa.CheckConstraint(
            "factor IN (0.5, 1.0, 1.5, 2.0)",
            name="ck_meal_portion_factors_supported",
        ),
        sa.ForeignKeyConstraint(["meal_id"], ["meals.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("meal_id", "factor"),
    )


def downgrade() -> None:
    op.drop_table("meal_portion_factors")
