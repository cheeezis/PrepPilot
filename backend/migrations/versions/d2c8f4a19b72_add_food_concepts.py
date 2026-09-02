"""add food concepts and remove the obsolete food inbox

Revision ID: d2c8f4a19b72
Revises: b7d2e4f91a63
Create Date: 2026-09-02

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d2c8f4a19b72"
down_revision: str | Sequence[str] | None = "b7d2e4f91a63"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM food_imports)
               OR EXISTS (SELECT 1 FROM foods WHERE origin = 'food_import') THEN
                RAISE EXCEPTION
                    'food_imports must be empty before simplifying the food model';
            END IF;
        END
        $$
        """
    )
    op.create_table(
        "food_concepts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.CheckConstraint(
            "length(trim(key)) > 0", name="ck_food_concepts_key_not_blank"
        ),
        sa.CheckConstraint(
            "length(trim(name)) > 0", name="ck_food_concepts_name_not_blank"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key"),
    )
    op.create_table(
        "food_source_identifiers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("concept_id", sa.Integer(), nullable=True),
        sa.Column("source_name", sa.String(length=100), nullable=False),
        sa.Column("external_id", sa.String(length=300), nullable=False),
        sa.Column("source_label", sa.String(length=300), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "length(trim(source_name)) > 0",
            name="ck_food_source_identifiers_source_not_blank",
        ),
        sa.CheckConstraint(
            "length(trim(external_id)) > 0",
            name="ck_food_source_identifiers_external_id_not_blank",
        ),
        sa.ForeignKeyConstraint(
            ["concept_id"], ["food_concepts.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source_name",
            "external_id",
            name="uq_food_source_identifiers_source_external",
        ),
    )

    op.add_column("foods", sa.Column("concept_id", sa.Integer(), nullable=True))
    op.add_column(
        "recipe_import_ingredients",
        sa.Column("concept_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "recipe_import_ingredients",
        sa.Column("source_identifier_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_recipe_import_ingredients_concept",
        "recipe_import_ingredients",
        "food_concepts",
        ["concept_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_recipe_import_ingredients_source_identifier",
        "recipe_import_ingredients",
        "food_source_identifiers",
        ["source_identifier_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.execute(
        """
        INSERT INTO food_concepts (key, name)
        SELECT catalog_key, name
        FROM foods
        ON CONFLICT (key) DO NOTHING
        """
    )
    op.execute(
        """
        UPDATE foods
        SET concept_id = food_concepts.id
        FROM food_concepts
        WHERE food_concepts.key = foods.catalog_key
        """
    )
    op.alter_column("foods", "concept_id", nullable=False)
    op.create_foreign_key(
        "fk_foods_concept",
        "foods",
        "food_concepts",
        ["concept_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    op.drop_constraint("ck_foods_origin_source", "foods", type_="check")
    op.drop_constraint("uq_foods_source_food_import", "foods", type_="unique")
    op.drop_constraint(
        "fk_foods_source_food_import", "foods", type_="foreignkey"
    )
    op.drop_column("foods", "source_food_import_id")
    op.drop_table("food_imports")
    sa.Enum(name="food_import_status").drop(op.get_bind(), checkfirst=True)


def downgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM foods WHERE origin = 'food_import') THEN
                RAISE EXCEPTION
                    'cannot reconstruct food import sources for imported foods';
            END IF;
        END
        $$
        """
    )
    food_import_status = sa.Enum(
        "ready_for_catalog_review",
        "needs_review",
        "rejected",
        name="food_import_status",
    )
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
    op.add_column(
        "foods",
        sa.Column("source_food_import_id", sa.Integer(), nullable=True),
    )
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

    op.drop_constraint(
        "fk_recipe_import_ingredients_source_identifier",
        "recipe_import_ingredients",
        type_="foreignkey",
    )
    op.drop_column("recipe_import_ingredients", "source_identifier_id")
    op.drop_constraint(
        "fk_recipe_import_ingredients_concept",
        "recipe_import_ingredients",
        type_="foreignkey",
    )
    op.drop_column("recipe_import_ingredients", "concept_id")
    op.drop_constraint("fk_foods_concept", "foods", type_="foreignkey")
    op.drop_column("foods", "concept_id")
    op.drop_table("food_source_identifiers")
    op.drop_table("food_concepts")
