from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Date,
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
        CheckConstraint(
            "category IN ('protein', 'carbohydrate', 'vegetable', 'dairy', "
            "'fat', 'sauce', 'spice', 'other')",
            name="ck_foods_category",
        ),
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
    category: Mapped[str] = mapped_column(String(20), server_default="other")
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


class WeeklyPlan(Base):
    __tablename__ = "weekly_plans"
    __table_args__ = (
        CheckConstraint("end_date >= start_date", name="ck_weekly_plans_date_order"),
        CheckConstraint(
            "snacks_per_day BETWEEN 0 AND 3",
            name="ck_weekly_plans_snacks_per_day",
        ),
        CheckConstraint(
            "calories_target_kcal > 0",
            name="ck_weekly_plans_calories_positive",
        ),
        CheckConstraint(
            "protein_minimum_g >= 0",
            name="ck_weekly_plans_protein_nonnegative",
        ),
        CheckConstraint(
            "carbohydrates_target_g >= 0",
            name="ck_weekly_plans_carbohydrates_nonnegative",
        ),
        CheckConstraint(
            "fat_maximum_g >= 0",
            name="ck_weekly_plans_fat_nonnegative",
        ),
        UniqueConstraint("start_date", "end_date", name="uq_weekly_plans_period"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    snacks_per_day: Mapped[int]
    calories_target_kcal: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    protein_minimum_g: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    carbohydrates_target_g: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    fat_maximum_g: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    assignments: Mapped[list["MealAssignment"]] = relationship(
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="MealAssignment.day_index, MealAssignment.meal_role, "
        "MealAssignment.slot_number",
    )


class MealAssignment(Base):
    __tablename__ = "meal_assignments"
    __table_args__ = (
        CheckConstraint(
            "day_index BETWEEN 0 AND 6",
            name="ck_meal_assignments_day_index",
        ),
        CheckConstraint(
            "meal_role IN ('breakfast', 'lunch', 'dinner', 'snack')",
            name="ck_meal_assignments_role",
        ),
        CheckConstraint(
            "(meal_role = 'snack' AND slot_number BETWEEN 1 AND 3) OR "
            "(meal_role <> 'snack' AND slot_number = 1)",
            name="ck_meal_assignments_slot_number",
        ),
        CheckConstraint(
            "portion_number IS NULL OR portion_number > 0",
            name="ck_meal_assignments_portion_positive",
        ),
        UniqueConstraint(
            "weekly_plan_id",
            "day_index",
            "meal_role",
            "slot_number",
            name="uq_meal_assignments_slot",
        ),
        UniqueConstraint(
            "weekly_plan_id",
            "recipe_id",
            "portion_number",
            name="uq_meal_assignments_batch_portion",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    weekly_plan_id: Mapped[int] = mapped_column(
        ForeignKey("weekly_plans.id", ondelete="CASCADE"), index=True
    )
    day_index: Mapped[int]
    meal_role: Mapped[str] = mapped_column(String(10))
    slot_number: Mapped[int]
    recipe_id: Mapped[int] = mapped_column(
        ForeignKey("recipes.id", ondelete="RESTRICT"), index=True
    )
    portion_number: Mapped[int | None]
    recipe: Mapped[Recipe] = relationship(lazy="joined")
