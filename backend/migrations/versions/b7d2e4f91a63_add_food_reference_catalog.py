"""add food reference catalog

Revision ID: b7d2e4f91a63
Revises: a91c5e73d204
Create Date: 2026-09-01

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b7d2e4f91a63"
down_revision: str | Sequence[str] | None = "a91c5e73d204"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "food_reference_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_name", sa.String(length=100), nullable=False),
        sa.Column("external_id", sa.String(length=200), nullable=False),
        sa.Column("data_type", sa.String(length=50), nullable=False),
        sa.Column("description", sa.String(length=300), nullable=False),
        sa.Column("normalized_description", sa.String(length=300), nullable=False),
        sa.Column("food_category", sa.String(length=200), nullable=True),
        sa.Column("publication_date", sa.String(length=20), nullable=True),
        sa.Column("dataset_release", sa.String(length=50), nullable=False),
        sa.Column("calories_per_100", sa.Numeric(10, 4), nullable=True),
        sa.Column("protein_per_100", sa.Numeric(10, 4), nullable=True),
        sa.Column("total_carbs_per_100", sa.Numeric(10, 4), nullable=True),
        sa.Column("fiber_per_100", sa.Numeric(10, 4), nullable=True),
        sa.Column("carbs_per_100", sa.Numeric(10, 4), nullable=True),
        sa.Column("fat_per_100", sa.Numeric(10, 4), nullable=True),
        sa.Column("portions", sa.JSON(), nullable=False),
        sa.Column("imported_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "length(trim(source_name)) > 0",
            name="ck_food_reference_items_source_name_not_blank",
        ),
        sa.CheckConstraint(
            "length(trim(external_id)) > 0",
            name="ck_food_reference_items_external_id_not_blank",
        ),
        sa.CheckConstraint(
            "length(trim(description)) > 0",
            name="ck_food_reference_items_description_not_blank",
        ),
        sa.CheckConstraint(
            "length(trim(normalized_description)) > 0",
            name="ck_food_reference_items_normalized_description_not_blank",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source_name",
            "external_id",
            name="uq_food_reference_items_source_external",
        ),
    )
    op.create_index(
        "ix_food_reference_items_normalized_description",
        "food_reference_items",
        ["normalized_description"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_food_reference_items_normalized_description",
        table_name="food_reference_items",
    )
    op.drop_table("food_reference_items")
