from dataclasses import dataclass
from decimal import Decimal
from typing import Mapping

from preppilot_api.catalog_data import FoodDefinition, MealDefinition


@dataclass(frozen=True)
class Nutrients:
    calories: Decimal = Decimal(0)
    protein: Decimal = Decimal(0)
    carbs: Decimal = Decimal(0)
    fat: Decimal = Decimal(0)

    def __add__(self, other: "Nutrients") -> "Nutrients":
        return Nutrients(
            calories=self.calories + other.calories,
            protein=self.protein + other.protein,
            carbs=self.carbs + other.carbs,
            fat=self.fat + other.fat,
        )

    def scaled(self, factor: Decimal) -> "Nutrients":
        return Nutrients(
            calories=self.calories * factor,
            protein=self.protein * factor,
            carbs=self.carbs * factor,
            fat=self.fat * factor,
        )


def calculate_meal_nutrients(
    meal: MealDefinition, foods: Mapping[str, FoodDefinition]
) -> Nutrients:
    nutrients = Nutrients()
    for ingredient in meal.ingredients:
        food = foods[ingredient.food_key]
        factor = ingredient.amount / Decimal(100)
        nutrients += Nutrients(
            calories=food.calories_per_100 * factor,
            protein=food.protein_per_100 * factor,
            carbs=food.carbs_per_100 * factor,
            fat=food.fat_per_100 * factor,
        )
    return nutrients
