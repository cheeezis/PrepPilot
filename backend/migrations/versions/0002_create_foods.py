"""Create the personal food catalog.

Revision ID: 0002_create_foods
Revises: 0001_v5_foundation
Create Date: 2026-09-04
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_create_foods"
down_revision: str | Sequence[str] | None = "0001_v5_foundation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "foods",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("base_unit", sa.String(length=2), nullable=False),
        sa.Column("calories_kcal", sa.Numeric(10, 2), nullable=False),
        sa.Column("protein_g", sa.Numeric(10, 2), nullable=False),
        sa.Column("carbohydrates_g", sa.Numeric(10, 2), nullable=False),
        sa.Column("fat_g", sa.Numeric(10, 2), nullable=False),
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
            "length(trim(name)) > 0", name="ck_foods_name_not_blank"
        ),
        sa.CheckConstraint("base_unit IN ('g', 'ml')", name="ck_foods_base_unit"),
        sa.CheckConstraint(
            "calories_kcal >= 0", name="ck_foods_calories_nonnegative"
        ),
        sa.CheckConstraint("protein_g >= 0", name="ck_foods_protein_nonnegative"),
        sa.CheckConstraint(
            "carbohydrates_g >= 0", name="ck_foods_carbohydrates_nonnegative"
        ),
        sa.CheckConstraint("fat_g >= 0", name="ck_foods_fat_nonnegative"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uq_foods_name_ci", "foods", [sa.text("lower(name)")], unique=True
    )


def downgrade() -> None:
    op.drop_index("uq_foods_name_ci", table_name="foods")
    op.drop_table("foods")
