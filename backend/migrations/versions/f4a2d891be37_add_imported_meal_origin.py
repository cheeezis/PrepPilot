"""add imported meal origin

Revision ID: f4a2d891be37
Revises: e7b61c3094ad
Create Date: 2026-08-31

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f4a2d891be37"
down_revision: str | Sequence[str] | None = "e7b61c3094ad"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    meal_origin = sa.Enum("curated_seed", "recipe_import", name="meal_origin")
    meal_origin.create(op.get_bind(), checkfirst=True)
    op.add_column("meals", sa.Column("origin", meal_origin, nullable=True))
    op.add_column(
        "meals",
        sa.Column("source_recipe_import_id", sa.Integer(), nullable=True),
    )
    op.execute("UPDATE meals SET origin = 'curated_seed'")
    op.alter_column("meals", "origin", nullable=False)
    op.create_foreign_key(
        "fk_meals_source_recipe_import",
        "meals",
        "recipe_imports",
        ["source_recipe_import_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_unique_constraint(
        "uq_meals_source_recipe_import",
        "meals",
        ["source_recipe_import_id"],
    )
    op.create_check_constraint(
        "ck_meals_origin_source",
        "meals",
        "(origin = 'curated_seed' AND source_recipe_import_id IS NULL) OR "
        "(origin = 'recipe_import' AND source_recipe_import_id IS NOT NULL)",
    )


def downgrade() -> None:
    op.drop_constraint("ck_meals_origin_source", "meals", type_="check")
    op.drop_constraint("uq_meals_source_recipe_import", "meals", type_="unique")
    op.drop_constraint(
        "fk_meals_source_recipe_import", "meals", type_="foreignkey"
    )
    op.drop_column("meals", "source_recipe_import_id")
    op.drop_column("meals", "origin")
    sa.Enum(name="meal_origin").drop(op.get_bind(), checkfirst=True)
