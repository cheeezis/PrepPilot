from collections import defaultdict
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from preppilot_api.models import (
    ImportedIngredientStatus,
    Meal,
    MealIngredient,
    MealOrigin,
    MealPortionFactor,
    MealRole,
    MealRoleAssignment,
    RecipeImportStatus,
)
from preppilot_api.recipe_imports import (
    get_recipe_import,
    ingredients_for_import,
)


class PromoteRecipeImportCommand(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    catalog_key: str = Field(pattern=r"^[a-z0-9_]+$", max_length=100)
    name: str = Field(min_length=1, max_length=200)
    preparation_minutes: int = Field(ge=0)
    instructions: str = Field(min_length=1)
    roles: tuple[MealRole, ...] = Field(min_length=1)
    portion_factors: tuple[Decimal, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_assignments(self) -> "PromoteRecipeImportCommand":
        if len(set(self.roles)) != len(self.roles):
            raise ValueError("roles must be unique")
        allowed_factors = {Decimal("0.5"), Decimal("1"), Decimal("1.5"), Decimal("2")}
        if any(factor not in allowed_factors for factor in self.portion_factors):
            raise ValueError("unsupported portion factor")
        if tuple(sorted(set(self.portion_factors))) != self.portion_factors:
            raise ValueError("portion factors must be unique and sorted")
        return self


class RecipePromotionError(ValueError):
    pass


def promote_recipe_import(
    session: Session,
    recipe_import_id: int,
    command: PromoteRecipeImportCommand,
) -> tuple[Meal, bool]:
    recipe_import = get_recipe_import(session, recipe_import_id)
    existing_promotion = session.scalar(
        select(Meal).where(Meal.source_recipe_import_id == recipe_import.id)
    )
    if existing_promotion is not None:
        return existing_promotion, False
    if recipe_import.status != RecipeImportStatus.READY_FOR_CATALOG_REVIEW:
        raise RecipePromotionError("recipe import is not ready for catalog review")
    if session.scalar(select(Meal.id).where(Meal.catalog_key == command.catalog_key)):
        raise RecipePromotionError("catalog_key already exists")

    amounts_by_food: defaultdict[int, Decimal] = defaultdict(Decimal)
    for ingredient in ingredients_for_import(session, recipe_import.id):
        if ingredient.status == ImportedIngredientStatus.EXCLUDED:
            continue
        if (
            ingredient.status != ImportedIngredientStatus.NORMALIZED
            or ingredient.food_id is None
            or ingredient.normalized_amount is None
        ):
            raise RecipePromotionError("recipe import contains incomplete ingredients")
        amounts_by_food[ingredient.food_id] += ingredient.normalized_amount
    if not amounts_by_food:
        raise RecipePromotionError("recipe import has no catalog ingredients")

    meal = Meal(
        catalog_key=command.catalog_key,
        name=command.name.strip(),
        preparation_minutes=command.preparation_minutes,
        instructions=command.instructions.strip(),
        origin=MealOrigin.RECIPE_IMPORT,
        source_recipe_import_id=recipe_import.id,
    )
    session.add(meal)
    session.flush()
    session.add_all(
        MealIngredient(meal_id=meal.id, food_id=food_id, amount=amount)
        for food_id, amount in sorted(amounts_by_food.items())
    )
    session.add_all(
        MealRoleAssignment(meal_id=meal.id, role=role) for role in command.roles
    )
    session.add_all(
        MealPortionFactor(meal_id=meal.id, factor=factor)
        for factor in command.portion_factors
    )
    session.flush()
    return meal, True
