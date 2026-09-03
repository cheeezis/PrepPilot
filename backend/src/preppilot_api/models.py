from decimal import Decimal

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Recipe(Base):
    __tablename__ = "recipes"
    __table_args__ = (
        CheckConstraint("length(trim(title)) > 0", name="ck_recipes_title"),
        CheckConstraint("servings > 0", name="ck_recipes_servings_positive"),
        CheckConstraint(
            "calories_per_serving > 0", name="ck_recipes_calories_positive"
        ),
        CheckConstraint(
            "protein_per_serving >= 0", name="ck_recipes_protein_nonnegative"
        ),
        CheckConstraint("carbs_per_serving >= 0", name="ck_recipes_carbs_nonnegative"),
        CheckConstraint("fat_per_serving >= 0", name="ck_recipes_fat_nonnegative"),
        CheckConstraint("sugar_per_serving >= 0", name="ck_recipes_sugar_nonnegative"),
        CheckConstraint(
            "saturated_fat_per_serving >= 0",
            name="ck_recipes_saturated_fat_nonnegative",
        ),
        CheckConstraint("fiber_per_serving >= 0", name="ck_recipes_fiber_nonnegative"),
        CheckConstraint("salt_per_serving >= 0", name="ck_recipes_salt_nonnegative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    source_url: Mapped[str | None] = mapped_column(Text)
    title: Mapped[str] = mapped_column(String(300))
    categories: Mapped[list[str]] = mapped_column(JSON)
    servings: Mapped[int] = mapped_column(Integer)
    calories_per_serving: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    protein_per_serving: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    carbs_per_serving: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    fat_per_serving: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    sugar_per_serving: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    saturated_fat_per_serving: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    fiber_per_serving: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    salt_per_serving: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    ingredients: Mapped[list[str]] = mapped_column(JSON)
    instructions: Mapped[list[str]] = mapped_column(JSON)
    preparation_minutes: Mapped[int | None] = mapped_column(Integer)
    cooking_minutes: Mapped[int | None] = mapped_column(Integer)
