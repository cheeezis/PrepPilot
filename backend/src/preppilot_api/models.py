from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
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


class Food(Base):
    __tablename__ = "foods"
    __table_args__ = (
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
    source_retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class FoodAlias(Base):
    __tablename__ = "food_aliases"
    __table_args__ = (
        CheckConstraint(
            "length(trim(source_name)) > 0",
            name="ck_food_aliases_source_name_not_blank",
        ),
        CheckConstraint(
            "length(trim(external_name)) > 0",
            name="ck_food_aliases_external_name_not_blank",
        ),
        CheckConstraint(
            "length(trim(normalized_name)) > 0",
            name="ck_food_aliases_normalized_name_not_blank",
        ),
    )

    source_name: Mapped[str] = mapped_column(String(200), primary_key=True)
    normalized_name: Mapped[str] = mapped_column(String(200), primary_key=True)
    external_name: Mapped[str] = mapped_column(String(200))
    food_id: Mapped[int] = mapped_column(
        ForeignKey("foods.id", ondelete="CASCADE"), index=True
    )


class FoodPortion(Base):
    __tablename__ = "food_portions"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_food_portions_amount_positive"),
        CheckConstraint(
            "gram_weight > 0",
            name="ck_food_portions_gram_weight_positive",
        ),
        CheckConstraint(
            "length(trim(unit)) > 0",
            name="ck_food_portions_unit_not_blank",
        ),
        CheckConstraint(
            "length(trim(source_name)) > 0",
            name="ck_food_portions_source_name_not_blank",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    food_id: Mapped[int] = mapped_column(
        ForeignKey("foods.id", ondelete="CASCADE"), index=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    unit: Mapped[str] = mapped_column(String(50))
    modifier: Mapped[str | None] = mapped_column(String(200))
    gram_weight: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    source_name: Mapped[str] = mapped_column(String(200))
    source_reference: Mapped[str | None] = mapped_column(Text)
    source_retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Meal(Base):
    __tablename__ = "meals"
    __table_args__ = (
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
            "length(trim(source_name)) > 0",
            name="ck_meals_source_name_not_blank",
        ),
        CheckConstraint(
            "source_servings IS NULL OR source_servings > 0",
            name="ck_meals_source_servings_positive",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    preparation_minutes: Mapped[int] = mapped_column(Integer)
    instructions: Mapped[str] = mapped_column(Text)
    source_name: Mapped[str] = mapped_column(String(200))
    source_reference: Mapped[str | None] = mapped_column(Text)
    source_retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    source_servings: Mapped[int | None] = mapped_column(Integer)


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
    source_measure: Mapped[str | None] = mapped_column(String(100))


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
