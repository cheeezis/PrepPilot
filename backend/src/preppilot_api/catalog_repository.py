from collections import defaultdict
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from preppilot_api.catalog_data import (
    Catalog,
    FoodDefinition,
    MealDefinition,
    MealIngredientDefinition,
)
from preppilot_api.models import (
    Food,
    FoodConcept,
    Meal,
    MealIngredient,
    MealPortionFactor,
    MealRole,
    MealRoleAssignment,
)


class CatalogUnavailableError(RuntimeError):
    pass


def load_catalog_from_database(session: Session) -> Catalog:
    foods = tuple(session.scalars(select(Food).order_by(Food.catalog_key)))
    meals = tuple(session.scalars(select(Meal).order_by(Meal.catalog_key)))
    if not foods or not meals:
        raise CatalogUnavailableError("Database catalog is empty")

    concepts_by_id = {
        concept.id: concept for concept in session.scalars(select(FoodConcept))
    }
    if any(food.concept_id not in concepts_by_id for food in foods):
        raise CatalogUnavailableError("Food references an unknown concept")

    food_keys_by_id = {food.id: food.catalog_key for food in foods}
    ingredients_by_meal: defaultdict[int, list[MealIngredientDefinition]] = defaultdict(
        list
    )
    for ingredient in session.scalars(
        select(MealIngredient).order_by(
            MealIngredient.meal_id,
            MealIngredient.food_id,
        )
    ):
        food_key = food_keys_by_id.get(ingredient.food_id)
        if food_key is None:
            raise CatalogUnavailableError("Ingredient references an unknown food")
        ingredients_by_meal[ingredient.meal_id].append(
            MealIngredientDefinition(
                food_key=food_key,
                amount=ingredient.amount,
            )
        )

    roles_by_meal: defaultdict[int, list[MealRole]] = defaultdict(list)
    for role_assignment in session.scalars(
        select(MealRoleAssignment).order_by(
            MealRoleAssignment.meal_id,
            MealRoleAssignment.role,
        )
    ):
        roles_by_meal[role_assignment.meal_id].append(role_assignment.role)

    factors_by_meal: defaultdict[int, list[Decimal]] = defaultdict(list)
    for factor_assignment in session.scalars(
        select(MealPortionFactor).order_by(
            MealPortionFactor.meal_id,
            MealPortionFactor.factor,
        )
    ):
        factors_by_meal[factor_assignment.meal_id].append(factor_assignment.factor)

    return Catalog(
        foods=tuple(
            FoodDefinition(
                key=food.catalog_key,
                name=food.name,
                concept_key=concepts_by_id[food.concept_id].key,
                concept_name=concepts_by_id[food.concept_id].name,
                brand=food.brand,
                unit=food.unit,
                calories_per_100=food.calories_per_100,
                protein_per_100=food.protein_per_100,
                carbs_per_100=food.carbs_per_100,
                fat_per_100=food.fat_per_100,
                source_name=food.source_name,
                source_reference=food.source_reference,
            )
            for food in foods
        ),
        meals=tuple(
            MealDefinition(
                key=meal.catalog_key,
                name=meal.name,
                preparation_minutes=meal.preparation_minutes,
                instructions=meal.instructions,
                roles=tuple(roles_by_meal[meal.id]),
                portion_factors=tuple(factors_by_meal[meal.id]),
                ingredients=tuple(ingredients_by_meal[meal.id]),
            )
            for meal in meals
        ),
    )
