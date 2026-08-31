from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from preppilot_api.catalog_data import Catalog, load_catalog
from preppilot_api.database import engine
from preppilot_api.models import (
    Food,
    Meal,
    MealIngredient,
    MealOrigin,
    MealPortionFactor,
    MealRoleAssignment,
)


def replace_catalog(session: Session, catalog: Catalog) -> None:
    existing_meals = {
        meal.catalog_key: meal for meal in session.scalars(select(Meal))
    }
    curated_meal_ids = {
        meal.id
        for meal in existing_meals.values()
        if meal.origin == MealOrigin.CURATED_SEED
    }
    if curated_meal_ids:
        session.execute(
            delete(MealRoleAssignment).where(
                MealRoleAssignment.meal_id.in_(curated_meal_ids)
            )
        )
        session.execute(
            delete(MealPortionFactor).where(
                MealPortionFactor.meal_id.in_(curated_meal_ids)
            )
        )
        session.execute(
            delete(MealIngredient).where(
                MealIngredient.meal_id.in_(curated_meal_ids)
            )
        )

    existing_foods = {
        food.catalog_key: food for food in session.scalars(select(Food))
    }
    foods: dict[str, Food] = {}
    for food_definition in catalog.foods:
        food = existing_foods.pop(food_definition.key, None)
        if food is None:
            food = Food(catalog_key=food_definition.key)
            session.add(food)
        food.name = food_definition.name
        food.brand = food_definition.brand
        food.unit = food_definition.unit
        food.calories_per_100 = food_definition.calories_per_100
        food.protein_per_100 = food_definition.protein_per_100
        food.carbs_per_100 = food_definition.carbs_per_100
        food.fat_per_100 = food_definition.fat_per_100
        food.source_name = food_definition.source_name
        food.source_reference = food_definition.source_reference
        foods[food_definition.key] = food

    for stale_food in existing_foods.values():
        session.delete(stale_food)

    session.flush()

    for meal_definition in catalog.meals:
        meal = existing_meals.pop(meal_definition.key, None)
        if meal is not None and meal.origin != MealOrigin.CURATED_SEED:
            raise ValueError(
                f"Seed meal key conflicts with imported meal: {meal.catalog_key}"
            )
        if meal is None:
            meal = Meal(
                catalog_key=meal_definition.key,
                origin=MealOrigin.CURATED_SEED,
                source_recipe_import_id=None,
            )
            session.add(meal)
        meal.name = meal_definition.name
        meal.preparation_minutes = meal_definition.preparation_minutes
        meal.instructions = meal_definition.instructions
        session.flush()
        session.add_all(
            MealIngredient(
                meal_id=meal.id,
                food_id=foods[ingredient.food_key].id,
                amount=ingredient.amount,
            )
            for ingredient in meal_definition.ingredients
        )
        session.add_all(
            MealRoleAssignment(meal_id=meal.id, role=role)
            for role in meal_definition.roles
        )
        session.add_all(
            MealPortionFactor(meal_id=meal.id, factor=factor)
            for factor in meal_definition.portion_factors
        )

    for stale_meal in existing_meals.values():
        if stale_meal.origin == MealOrigin.CURATED_SEED:
            session.delete(stale_meal)


def main() -> None:
    catalog = load_catalog()
    with Session(engine) as session, session.begin():
        replace_catalog(session, catalog)
    print(f"Loaded {len(catalog.foods)} foods and {len(catalog.meals)} meals")


if __name__ == "__main__":
    main()
