"""replace recipe category with categories

Revision ID: c4e8a1f6b209
Revises: 8c2f7d4a9e11
Create Date: 2026-09-03
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c4e8a1f6b209"
down_revision: str | None = "8c2f7d4a9e11"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("recipes", sa.Column("categories", sa.JSON(), nullable=True))
    op.execute("UPDATE recipes SET categories = json_build_array(category)")
    op.alter_column("recipes", "categories", nullable=False)
    op.drop_constraint("ck_recipes_category", "recipes", type_="check")
    op.drop_column("recipes", "category")


def downgrade() -> None:
    op.add_column(
        "recipes",
        sa.Column("category", sa.String(length=20), nullable=True),
    )
    op.execute(
        """
        UPDATE recipes
        SET category = CASE
            WHEN categories->>0 IN ('breakfast', 'lunch', 'dinner')
            THEN categories->>0
            ELSE 'dinner'
        END
        """
    )
    op.alter_column("recipes", "category", nullable=False)
    op.create_check_constraint(
        "ck_recipes_category",
        "recipes",
        "category in ('breakfast', 'lunch', 'dinner')",
    )
    op.drop_column("recipes", "categories")
