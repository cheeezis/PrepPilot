"""add food import inbox

Revision ID: a91c5e73d204
Revises: f4a2d891be37
Create Date: 2026-08-31

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a91c5e73d204"
down_revision: str | Sequence[str] | None = "f4a2d891be37"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    food_import_status = sa.Enum(
        "ready_for_catalog_review",
        "needs_review",
        "rejected",
        name="food_import_status",
    )
    food_origin = sa.Enum("curated_seed", "food_import", name="food_origin")
    food_origin.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "food_imports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_name", sa.String(length=100), nullable=False),
        sa.Column("external_id", sa.String(length=200), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("raw_payload", sa.JSON(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("status", food_import_status, nullable=False),
        sa.Column("candidate_name", sa.String(length=300), nullable=True),
        sa.Column("calories_per_100", sa.Numeric(10, 4), nullable=True),
        sa.Column("protein_per_100", sa.Numeric(10, 4), nullable=True),
        sa.Column("carbs_per_100", sa.Numeric(10, 4), nullable=True),
        sa.Column("fat_per_100", sa.Numeric(10, 4), nullable=True),
        sa.Column("review_reasons", sa.JSON(), nullable=False),
        sa.CheckConstraint(
            "length(trim(source_name)) > 0",
            name="ck_food_imports_source_name_not_blank",
        ),
        sa.CheckConstraint(
            "length(trim(external_id)) > 0",
            name="ck_food_imports_external_id_not_blank",
        ),
        sa.CheckConstraint(
            "length(content_hash) = 64",
            name="ck_food_imports_content_hash_sha256",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source_name",
            "external_id",
            "content_hash",
            name="uq_food_imports_source_external_content",
        ),
    )
    op.add_column("foods", sa.Column("origin", food_origin, nullable=True))
    op.add_column(
        "foods", sa.Column("source_food_import_id", sa.Integer(), nullable=True)
    )
    op.execute("UPDATE foods SET origin = 'curated_seed'")
    op.alter_column("foods", "origin", nullable=False)
    op.create_foreign_key(
        "fk_foods_source_food_import",
        "foods",
        "food_imports",
        ["source_food_import_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_unique_constraint(
        "uq_foods_source_food_import", "foods", ["source_food_import_id"]
    )
    op.create_check_constraint(
        "ck_foods_origin_source",
        "foods",
        "(origin = 'curated_seed' AND source_food_import_id IS NULL) OR "
        "(origin = 'food_import' AND source_food_import_id IS NOT NULL)",
    )


def downgrade() -> None:
    op.drop_constraint("ck_foods_origin_source", "foods", type_="check")
    op.drop_constraint("uq_foods_source_food_import", "foods", type_="unique")
    op.drop_constraint("fk_foods_source_food_import", "foods", type_="foreignkey")
    op.drop_column("foods", "source_food_import_id")
    op.drop_column("foods", "origin")
    op.drop_table("food_imports")
    sa.Enum(name="food_origin").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="food_import_status").drop(op.get_bind(), checkfirst=True)
