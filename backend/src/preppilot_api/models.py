from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Food(Base):
    __tablename__ = "foods"
    __table_args__ = (
        CheckConstraint("length(trim(name)) > 0", name="ck_foods_name_not_blank"),
        CheckConstraint("base_unit IN ('g', 'ml')", name="ck_foods_base_unit"),
        CheckConstraint("calories_kcal >= 0", name="ck_foods_calories_nonnegative"),
        CheckConstraint("protein_g >= 0", name="ck_foods_protein_nonnegative"),
        CheckConstraint(
            "carbohydrates_g >= 0", name="ck_foods_carbohydrates_nonnegative"
        ),
        CheckConstraint("fat_g >= 0", name="ck_foods_fat_nonnegative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    base_unit: Mapped[str] = mapped_column(String(2))
    calories_kcal: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    protein_g: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    carbohydrates_g: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    fat_g: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


Index("uq_foods_name_ci", func.lower(Food.name), unique=True)


class Recipe(Base):
    __tablename__ = "recipes"
    __table_args__ = (
        CheckConstraint("length(trim(title)) > 0", name="ck_recipes_title_not_blank"),
        CheckConstraint("servings > 0", name="ck_recipes_servings_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(300))
    servings: Mapped[int]
    instructions: Mapped[list[str]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    meal_roles: Mapped[list["RecipeMealRole"]] = relationship(
        cascade="all, delete-orphan", lazy="selectin"
    )
    ingredients: Mapped[list["RecipeIngredient"]] = relationship(
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="RecipeIngredient.position",
    )


class RecipeMealRole(Base):
    __tablename__ = "recipe_meal_roles"
    __table_args__ = (
        CheckConstraint(
            "meal_role IN ('breakfast', 'lunch', 'dinner', 'snack')",
            name="ck_recipe_meal_roles_value",
        ),
    )

    recipe_id: Mapped[int] = mapped_column(
        ForeignKey("recipes.id", ondelete="CASCADE"), primary_key=True
    )
    meal_role: Mapped[str] = mapped_column(String(10), primary_key=True)


class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_recipe_ingredients_amount_positive"),
        CheckConstraint(
            "unit IN ('g', 'ml')", name="ck_recipe_ingredients_unit"
        ),
        CheckConstraint(
            "position >= 0", name="ck_recipe_ingredients_position_nonnegative"
        ),
        UniqueConstraint(
            "recipe_id", "position", name="uq_recipe_ingredients_position"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    recipe_id: Mapped[int] = mapped_column(
        ForeignKey("recipes.id", ondelete="CASCADE"), index=True
    )
    food_id: Mapped[int] = mapped_column(
        ForeignKey("foods.id", ondelete="RESTRICT"), index=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    unit: Mapped[str] = mapped_column(String(2))
    position: Mapped[int]
    food: Mapped[Food] = relationship(lazy="joined")
