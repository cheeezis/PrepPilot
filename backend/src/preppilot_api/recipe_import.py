from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from preppilot_api.measurements import parse_measurement
from preppilot_api.models import (
    Food,
    FoodPortion,
    Meal,
    MealIngredient,
    MealRole,
    MealRoleAssignment,
)
from preppilot_api.portion_conversion import convert_measurement
from preppilot_api.themealdb import Recipe


class RecipeSource(Protocol):
    def get_recipe(self, meal_id: str) -> Recipe: ...


class IngredientResolver(Protocol):
    def resolve(
        self, session: Session, source_name: str, external_name: str
    ) -> Food: ...


@dataclass(frozen=True)
class RecipeImportOptions:
    source_servings: int
    preparation_minutes: int
    role: MealRole

    def __post_init__(self) -> None:
        if self.source_servings <= 0:
            raise ValueError("Source servings must be positive")
        if self.preparation_minutes < 0:
            raise ValueError("Preparation minutes must not be negative")


def import_themealdb_recipe(
    session: Session,
    meal_id: str,
    options: RecipeImportOptions,
    recipe_source: RecipeSource,
    ingredient_resolver: IngredientResolver,
) -> Meal:
    recipe = recipe_source.get_recipe(meal_id)
    with session.begin():
        meal = Meal(
            name=recipe.name,
            preparation_minutes=options.preparation_minutes,
            instructions=recipe.instructions,
            source_name="themealdb",
            source_reference=recipe.source_id,
            source_retrieved_at=datetime.now(UTC),
            source_servings=options.source_servings,
        )
        session.add(meal)
        session.flush()

        for ingredient in recipe.ingredients:
            food = ingredient_resolver.resolve(
                session,
                source_name="themealdb",
                external_name=ingredient.name,
            )
            portions = session.scalars(
                select(FoodPortion).where(FoodPortion.food_id == food.id)
            )
            normalized = convert_measurement(
                parse_measurement(ingredient.measure),
                food.unit,
                portions,
            )
            session.add(
                MealIngredient(
                    meal_id=meal.id,
                    food_id=food.id,
                    amount=normalized.amount / Decimal(options.source_servings),
                    source_measure=ingredient.measure,
                )
            )

        session.add(MealRoleAssignment(meal_id=meal.id, role=options.role))

    return meal
