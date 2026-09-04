from dataclasses import dataclass
from decimal import Decimal

from preppilot_api.models import Recipe


@dataclass(frozen=True)
class Nutrients:
    calories_kcal: Decimal = Decimal(0)
    protein_g: Decimal = Decimal(0)
    carbohydrates_g: Decimal = Decimal(0)
    fat_g: Decimal = Decimal(0)

    def __add__(self, other: "Nutrients") -> "Nutrients":
        return Nutrients(
            calories_kcal=self.calories_kcal + other.calories_kcal,
            protein_g=self.protein_g + other.protein_g,
            carbohydrates_g=self.carbohydrates_g + other.carbohydrates_g,
            fat_g=self.fat_g + other.fat_g,
        )

    def divided_by(self, divisor: int) -> "Nutrients":
        return Nutrients(
            calories_kcal=self.calories_kcal / divisor,
            protein_g=self.protein_g / divisor,
            carbohydrates_g=self.carbohydrates_g / divisor,
            fat_g=self.fat_g / divisor,
        )


@dataclass(frozen=True)
class RecipeNutrition:
    total: Nutrients
    per_serving: Nutrients


def calculate_recipe_nutrition(recipe: Recipe) -> RecipeNutrition:
    total = Nutrients()
    for ingredient in recipe.ingredients:
        base_amount = ingredient.amount
        if ingredient.food_portion is not None:
            base_amount *= ingredient.food_portion.amount
        factor = base_amount / Decimal(100)
        total += Nutrients(
            calories_kcal=ingredient.food.calories_kcal * factor,
            protein_g=ingredient.food.protein_g * factor,
            carbohydrates_g=ingredient.food.carbohydrates_g * factor,
            fat_g=ingredient.food.fat_g * factor,
        )
    return RecipeNutrition(total=total, per_serving=total.divided_by(recipe.servings))
