from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class MeasurementUnit(StrEnum):
    GRAM = "g"
    MILLILITER = "ml"


class MealRole(StrEnum):
    FIRST_MEAL = "first_meal"
    QUICK_LUNCH = "quick_lunch"
    PROTEIN_SNACK = "protein_snack"
    MAIN_MEAL = "main_meal"
    LATE_SNACK = "late_snack"


class RecipeImportStatus(StrEnum):
    RECEIVED = "received"
    READY_FOR_CATALOG_REVIEW = "ready_for_catalog_review"
    NEEDS_REVIEW = "needs_review"
    REJECTED = "rejected"


class ImportedIngredientStatus(StrEnum):
    NORMALIZED = "normalized"
    NEEDS_REVIEW = "needs_review"
    EXCLUDED = "excluded"


class ImportReviewReason(StrEnum):
    UNKNOWN_FOOD = "unknown_food"
    AMBIGUOUS_FOOD = "ambiguous_food"
    UNSUPPORTED_UNIT = "unsupported_unit"
    MISSING_MEASURE_DEFAULT = "missing_measure_default"
    INVALID_OR_RANGED_QUANTITY = "invalid_or_ranged_quantity"
    INCOMPATIBLE_MEASUREMENT = "incompatible_measurement"
    MISSING_SERVING_COUNT = "missing_serving_count"


class ReviewDecisionAction(StrEnum):
    ASSIGN_FOOD = "assign_food"
    ADD_ALIAS = "add_alias"
    ADD_MEASURE_DEFAULT = "add_measure_default"
    OVERRIDE_AMOUNT = "override_amount"
    EXCLUDE = "exclude"
    SET_SERVINGS = "set_servings"
    REJECT = "reject"


class MealOrigin(StrEnum):
    CURATED_SEED = "curated_seed"
    RECIPE_IMPORT = "recipe_import"


class Food(Base):
    __tablename__ = "foods"
    __table_args__ = (
        CheckConstraint(
            "length(trim(catalog_key)) > 0", name="ck_foods_catalog_key_not_blank"
        ),
        CheckConstraint("length(trim(name)) > 0", name="ck_foods_name_not_blank"),
        CheckConstraint(
            "length(trim(source_name)) > 0",
            name="ck_foods_source_name_not_blank",
        ),
        CheckConstraint("calories_per_100 >= 0", name="ck_foods_calories_nonnegative"),
        CheckConstraint("protein_per_100 >= 0", name="ck_foods_protein_nonnegative"),
        CheckConstraint("carbs_per_100 >= 0", name="ck_foods_carbs_nonnegative"),
        CheckConstraint("fat_per_100 >= 0", name="ck_foods_fat_nonnegative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    catalog_key: Mapped[str] = mapped_column(String(100), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    brand: Mapped[str | None] = mapped_column(String(200))
    unit: Mapped[MeasurementUnit] = mapped_column(
        SqlEnum(
            MeasurementUnit,
            name="measurement_unit",
            values_callable=lambda enum_class: [member.value for member in enum_class],
        )
    )
    calories_per_100: Mapped[Decimal] = mapped_column(Numeric(10, 4))
    protein_per_100: Mapped[Decimal] = mapped_column(Numeric(10, 4))
    carbs_per_100: Mapped[Decimal] = mapped_column(Numeric(10, 4))
    fat_per_100: Mapped[Decimal] = mapped_column(Numeric(10, 4))
    source_name: Mapped[str] = mapped_column(String(200))
    source_reference: Mapped[str | None] = mapped_column(Text)


class Meal(Base):
    __tablename__ = "meals"
    __table_args__ = (
        CheckConstraint(
            "length(trim(catalog_key)) > 0", name="ck_meals_catalog_key_not_blank"
        ),
        CheckConstraint("length(trim(name)) > 0", name="ck_meals_name_not_blank"),
        CheckConstraint(
            "preparation_minutes >= 0",
            name="ck_meals_preparation_minutes_nonnegative",
        ),
        CheckConstraint(
            "length(trim(instructions)) > 0",
            name="ck_meals_instructions_not_blank",
        ),
        CheckConstraint(
            "(origin = 'curated_seed' AND source_recipe_import_id IS NULL) OR "
            "(origin = 'recipe_import' AND source_recipe_import_id IS NOT NULL)",
            name="ck_meals_origin_source",
        ),
        UniqueConstraint(
            "source_recipe_import_id", name="uq_meals_source_recipe_import"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    catalog_key: Mapped[str] = mapped_column(String(100), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    preparation_minutes: Mapped[int] = mapped_column(Integer)
    instructions: Mapped[str] = mapped_column(Text)
    origin: Mapped[MealOrigin] = mapped_column(
        SqlEnum(
            MealOrigin,
            name="meal_origin",
            values_callable=lambda enum_class: [member.value for member in enum_class],
        )
    )
    source_recipe_import_id: Mapped[int | None] = mapped_column(
        ForeignKey("recipe_imports.id", ondelete="RESTRICT")
    )


class MealIngredient(Base):
    __tablename__ = "meal_ingredients"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_meal_ingredients_amount_positive"),
    )

    meal_id: Mapped[int] = mapped_column(
        ForeignKey("meals.id", ondelete="CASCADE"), primary_key=True
    )
    food_id: Mapped[int] = mapped_column(
        ForeignKey("foods.id", ondelete="CASCADE"), primary_key=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 3))


class MealPortionFactor(Base):
    __tablename__ = "meal_portion_factors"
    __table_args__ = (
        CheckConstraint(
            "factor IN (0.5, 1.0, 1.5, 2.0)",
            name="ck_meal_portion_factors_supported",
        ),
    )

    meal_id: Mapped[int] = mapped_column(
        ForeignKey("meals.id", ondelete="CASCADE"), primary_key=True
    )
    factor: Mapped[Decimal] = mapped_column(Numeric(2, 1), primary_key=True)


class MealRoleAssignment(Base):
    __tablename__ = "meal_roles"

    meal_id: Mapped[int] = mapped_column(
        ForeignKey("meals.id", ondelete="CASCADE"), primary_key=True
    )
    role: Mapped[MealRole] = mapped_column(
        SqlEnum(
            MealRole,
            name="meal_role",
            values_callable=lambda enum_class: [member.value for member in enum_class],
        ),
        primary_key=True,
    )


class RecipeImport(Base):
    __tablename__ = "recipe_imports"
    __table_args__ = (
        CheckConstraint(
            "length(trim(source_name)) > 0",
            name="ck_recipe_imports_source_name_not_blank",
        ),
        CheckConstraint(
            "length(trim(external_id)) > 0",
            name="ck_recipe_imports_external_id_not_blank",
        ),
        CheckConstraint(
            "length(content_hash) = 64",
            name="ck_recipe_imports_content_hash_sha256",
        ),
        CheckConstraint(
            "manual_servings IS NULL OR manual_servings > 0",
            name="ck_recipe_imports_manual_servings_positive",
        ),
        UniqueConstraint(
            "source_name",
            "external_id",
            "content_hash",
            name="uq_recipe_imports_source_external_content",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    source_name: Mapped[str] = mapped_column(String(100))
    external_id: Mapped[str] = mapped_column(String(200))
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    raw_payload: Mapped[dict[str, object]] = mapped_column(JSON)
    content_hash: Mapped[str] = mapped_column(String(64))
    raw_servings: Mapped[str | None] = mapped_column(String(100))
    manual_servings: Mapped[Decimal | None] = mapped_column(Numeric(10, 3))
    status: Mapped[RecipeImportStatus] = mapped_column(
        SqlEnum(
            RecipeImportStatus,
            name="recipe_import_status",
            values_callable=lambda enum_class: [member.value for member in enum_class],
        )
    )


class RecipeImportIngredient(Base):
    __tablename__ = "recipe_import_ingredients"
    __table_args__ = (
        CheckConstraint("position >= 0", name="ck_import_ingredients_position"),
        CheckConstraint(
            "length(trim(raw_line)) > 0",
            name="ck_import_ingredients_raw_line_not_blank",
        ),
        CheckConstraint(
            "length(trim(raw_name)) > 0",
            name="ck_import_ingredients_raw_name_not_blank",
        ),
        CheckConstraint(
            "manual_amount IS NULL OR manual_amount > 0",
            name="ck_import_ingredients_manual_amount_positive",
        ),
        CheckConstraint(
            "normalized_amount IS NULL OR normalized_amount > 0",
            name="ck_import_ingredients_normalized_amount_positive",
        ),
        UniqueConstraint(
            "recipe_import_id",
            "position",
            name="uq_import_ingredients_recipe_position",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    recipe_import_id: Mapped[int] = mapped_column(
        ForeignKey("recipe_imports.id", ondelete="CASCADE")
    )
    position: Mapped[int] = mapped_column(Integer)
    raw_line: Mapped[str] = mapped_column(Text)
    raw_name: Mapped[str] = mapped_column(String(300))
    raw_amount: Mapped[str | None] = mapped_column(String(100))
    raw_unit: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[ImportedIngredientStatus] = mapped_column(
        SqlEnum(
            ImportedIngredientStatus,
            name="imported_ingredient_status",
            values_callable=lambda enum_class: [member.value for member in enum_class],
        )
    )
    review_reason: Mapped[ImportReviewReason | None] = mapped_column(
        SqlEnum(
            ImportReviewReason,
            name="import_review_reason",
            values_callable=lambda enum_class: [member.value for member in enum_class],
        )
    )
    food_id: Mapped[int | None] = mapped_column(
        ForeignKey("foods.id", ondelete="SET NULL")
    )
    manual_food_id: Mapped[int | None] = mapped_column(
        ForeignKey("foods.id", ondelete="SET NULL")
    )
    normalized_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 3))
    manual_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 3))
    excluded: Mapped[bool] = mapped_column(Boolean, default=False)


class FoodAlias(Base):
    __tablename__ = "food_aliases"
    __table_args__ = (
        CheckConstraint(
            "length(trim(alias)) > 0", name="ck_food_aliases_alias_not_blank"
        ),
        CheckConstraint(
            "length(trim(normalized_alias)) > 0",
            name="ck_food_aliases_normalized_alias_not_blank",
        ),
        UniqueConstraint(
            "normalized_alias", name="uq_food_aliases_normalized_alias"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    alias: Mapped[str] = mapped_column(String(300))
    normalized_alias: Mapped[str] = mapped_column(String(300))
    food_id: Mapped[int] = mapped_column(ForeignKey("foods.id", ondelete="CASCADE"))
    source_name: Mapped[str | None] = mapped_column(String(100))


class FoodMeasureDefault(Base):
    __tablename__ = "food_measure_defaults"
    __table_args__ = (
        CheckConstraint(
            "length(trim(measure_key)) > 0",
            name="ck_food_measure_defaults_key_not_blank",
        ),
        CheckConstraint("amount > 0", name="ck_food_measure_defaults_amount_positive"),
        CheckConstraint(
            "length(trim(source_name)) > 0",
            name="ck_food_measure_defaults_source_not_blank",
        ),
        UniqueConstraint(
            "food_id",
            "measure_key",
            name="uq_food_measure_defaults_food_measure",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    food_id: Mapped[int] = mapped_column(ForeignKey("foods.id", ondelete="CASCADE"))
    measure_key: Mapped[str] = mapped_column(String(100))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    source_name: Mapped[str] = mapped_column(String(200))
    source_reference: Mapped[str | None] = mapped_column(Text)


class ImportReviewDecision(Base):
    __tablename__ = "import_review_decisions"

    id: Mapped[int] = mapped_column(primary_key=True)
    recipe_import_id: Mapped[int] = mapped_column(
        ForeignKey("recipe_imports.id", ondelete="CASCADE")
    )
    ingredient_id: Mapped[int | None] = mapped_column(
        ForeignKey("recipe_import_ingredients.id", ondelete="CASCADE")
    )
    action: Mapped[ReviewDecisionAction] = mapped_column(
        SqlEnum(
            ReviewDecisionAction,
            name="review_decision_action",
            values_callable=lambda enum_class: [member.value for member in enum_class],
        )
    )
    details: Mapped[dict[str, object]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
