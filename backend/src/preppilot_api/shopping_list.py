from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from preppilot_api.models import Food, WeeklyPlan

AMOUNT_PRECISION = Decimal("0.001")
SHOPPING_UNITS = {
    "Becher",
    "Bund",
    "Dose",
    "Filet",
    "Kopf",
    "Packung",
    "Stück",
    "Zehe",
}


@dataclass(frozen=True)
class ShoppingListItem:
    food: Food
    amount: Decimal
    equivalent_amount: int | None
    equivalent_unit: str | None


def calculate_shopping_list(plan: WeeklyPlan) -> list[ShoppingListItem]:
    recipe_counts: dict[int, int] = {}
    recipes = {}
    for assignment in plan.assignments:
        recipe_counts[assignment.recipe_id] = (
            recipe_counts.get(assignment.recipe_id, 0) + 1
        )
        recipes[assignment.recipe_id] = assignment.recipe

    totals: dict[int, Decimal] = {}
    foods: dict[int, Food] = {}
    for recipe_id, count in recipe_counts.items():
        recipe = recipes[recipe_id]
        consumption = Decimal(count) / Decimal(recipe.servings)
        for ingredient in recipe.ingredients:
            amount = ingredient.amount
            if ingredient.food_portion is not None:
                amount *= ingredient.food_portion.amount
            totals[ingredient.food_id] = (
                totals.get(ingredient.food_id, Decimal(0)) + amount * consumption
            )
            foods[ingredient.food_id] = ingredient.food

    items = [
        _shopping_list_item(foods[food_id], amount)
        for food_id, amount in totals.items()
    ]
    return sorted(items, key=lambda item: (item.food.category, item.food.name.casefold()))


def _shopping_list_item(food: Food, amount: Decimal) -> ShoppingListItem:
    rounded = amount.quantize(AMOUNT_PRECISION, rounding=ROUND_HALF_UP)
    for portion in food.portions:
        if portion.name not in SHOPPING_UNITS:
            continue
        equivalent = rounded / portion.amount
        if equivalent == equivalent.to_integral_value():
            return ShoppingListItem(
                food=food,
                amount=rounded,
                equivalent_amount=int(equivalent),
                equivalent_unit=portion.name,
            )
    return ShoppingListItem(
        food=food,
        amount=rounded,
        equivalent_amount=None,
        equivalent_unit=None,
    )
