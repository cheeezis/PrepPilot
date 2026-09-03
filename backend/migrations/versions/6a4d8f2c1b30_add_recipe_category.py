"""add recipe category

Revision ID: 6a4d8f2c1b30
Revises: 1d2c4b6a8e10
Create Date: 2026-09-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "6a4d8f2c1b30"
down_revision: str | None = "1d2c4b6a8e10"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "recipes",
        sa.Column(
            "category",
            sa.String(length=20),
            nullable=False,
            server_default="dinner",
        ),
    )
    op.create_check_constraint(
        "ck_recipes_category",
        "recipes",
        "category in ('breakfast', 'lunch', 'dinner')",
    )
    op.alter_column("recipes", "category", server_default=None)


def downgrade() -> None:
    op.drop_constraint("ck_recipes_category", "recipes", type_="check")
    op.drop_column("recipes", "category")
