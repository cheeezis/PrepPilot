"""create recipe-first schema

Revision ID: 1d2c4b6a8e10
Revises:
Create Date: 2026-09-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "1d2c4b6a8e10"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "recipes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_name", sa.String(length=100), nullable=False),
        sa.Column("external_id", sa.String(length=300), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("servings", sa.Integer(), nullable=False),
        sa.Column("calories_per_serving", sa.Numeric(10, 2), nullable=False),
        sa.Column("protein_per_serving", sa.Numeric(10, 2), nullable=False),
        sa.Column("carbs_per_serving", sa.Numeric(10, 2), nullable=False),
        sa.Column("fat_per_serving", sa.Numeric(10, 2), nullable=False),
        sa.Column("ingredients", sa.JSON(), nullable=False),
        sa.Column("instructions", sa.JSON(), nullable=False),
        sa.Column("preparation_minutes", sa.Integer(), nullable=True),
        sa.Column("cooking_minutes", sa.Integer(), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("imported_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("license_name", sa.String(length=200), nullable=False),
        sa.Column("attribution_text", sa.Text(), nullable=False),
        sa.CheckConstraint("length(trim(source_name)) > 0", name="ck_recipes_source"),
        sa.CheckConstraint(
            "length(trim(external_id)) > 0", name="ck_recipes_external_id"
        ),
        sa.CheckConstraint(
            "length(trim(source_url)) > 0", name="ck_recipes_source_url"
        ),
        sa.CheckConstraint("length(trim(title)) > 0", name="ck_recipes_title"),
        sa.CheckConstraint("servings > 0", name="ck_recipes_servings_positive"),
        sa.CheckConstraint(
            "calories_per_serving > 0", name="ck_recipes_calories_positive"
        ),
        sa.CheckConstraint(
            "protein_per_serving >= 0", name="ck_recipes_protein_nonnegative"
        ),
        sa.CheckConstraint(
            "carbs_per_serving >= 0", name="ck_recipes_carbs_nonnegative"
        ),
        sa.CheckConstraint("fat_per_serving >= 0", name="ck_recipes_fat_nonnegative"),
        sa.CheckConstraint("length(content_hash) = 64", name="ck_recipes_content_hash"),
        sa.UniqueConstraint(
            "source_name", "external_id", name="uq_recipes_source_external"
        ),
    )


def downgrade() -> None:
    op.drop_table("recipes")
