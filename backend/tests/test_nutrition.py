from decimal import Decimal

from preppilot_api.catalog_data import load_catalog
from preppilot_api.nutrition import Nutrients, calculate_meal_nutrients


def test_calculates_meal_nutrients_from_normalized_ingredients() -> None:
    catalog = load_catalog()
    foods = {food.key: food for food in catalog.foods}
    meal = next(meal for meal in catalog.meals if meal.key == "whey_shake")

    assert calculate_meal_nutrients(meal, foods) == Nutrients(
        calories=Decimal("293"),
        protein=Decimal("40.2"),
        carbs=Decimal("17.9"),
        fat=Decimal("6.9"),
    )


def test_every_catalog_meal_has_positive_energy_and_protein() -> None:
    catalog = load_catalog()
    foods = {food.key: food for food in catalog.foods}

    for meal in catalog.meals:
        nutrients = calculate_meal_nutrients(meal, foods)
        assert nutrients.calories > 0, meal.key
        assert nutrients.protein > 0, meal.key
