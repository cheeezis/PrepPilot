from decimal import Decimal
from enum import StrEnum

from sqlalchemy import CheckConstraint, ForeignKey, Integer, Numeric, String, Text
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
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    catalog_key: Mapped[str] = mapped_column(String(100), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    preparation_minutes: Mapped[int] = mapped_column(Integer)
    instructions: Mapped[str] = mapped_column(Text)


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
