"""support custom recipes

Revision ID: f7b3c9d2a641
Revises: c4e8a1f6b209
Create Date: 2026-09-03
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f7b3c9d2a641"
down_revision: str | None = "c4e8a1f6b209"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

REMOVED_COLUMNS = (
    "source_name",
    "external_id",
    "raw_payload",
    "content_hash",
    "imported_at",
    "license_name",
    "attribution_text",
)


def upgrade() -> None:
    op.execute("DELETE FROM recipes")
    op.drop_constraint("uq_recipes_source_external", "recipes", type_="unique")
    op.drop_constraint("ck_recipes_source", "recipes", type_="check")
    op.drop_constraint("ck_recipes_external_id", "recipes", type_="check")
    op.drop_constraint("ck_recipes_source_url", "recipes", type_="check")
    op.drop_constraint("ck_recipes_content_hash", "recipes", type_="check")
    for column_name in REMOVED_COLUMNS:
        op.drop_column("recipes", column_name)
    op.alter_column("recipes", "source_url", existing_type=sa.Text(), nullable=True)


def downgrade() -> None:
    op.execute("DELETE FROM recipes")
    op.alter_column("recipes", "source_url", existing_type=sa.Text(), nullable=False)
    op.add_column("recipes", sa.Column("source_name", sa.String(100), nullable=False))
    op.add_column("recipes", sa.Column("external_id", sa.String(300), nullable=False))
    op.add_column("recipes", sa.Column("raw_payload", sa.JSON(), nullable=False))
    op.add_column("recipes", sa.Column("content_hash", sa.String(64), nullable=False))
    op.add_column(
        "recipes", sa.Column("imported_at", sa.DateTime(timezone=True), nullable=False)
    )
    op.add_column("recipes", sa.Column("license_name", sa.String(200), nullable=False))
    op.add_column("recipes", sa.Column("attribution_text", sa.Text(), nullable=False))
    op.create_check_constraint(
        "ck_recipes_source", "recipes", "length(trim(source_name)) > 0"
    )
    op.create_check_constraint(
        "ck_recipes_external_id", "recipes", "length(trim(external_id)) > 0"
    )
    op.create_check_constraint(
        "ck_recipes_source_url", "recipes", "length(trim(source_url)) > 0"
    )
    op.create_check_constraint(
        "ck_recipes_content_hash", "recipes", "length(content_hash) = 64"
    )
    op.create_unique_constraint(
        "uq_recipes_source_external", "recipes", ["source_name", "external_id"]
    )
