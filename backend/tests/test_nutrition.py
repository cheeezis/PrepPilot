from decimal import Decimal

from preppilot_api.models import Food, FoodPortion, Recipe, RecipeIngredient
from preppilot_api.nutrition import Nutrients, calculate_recipe_nutrition


def test_recipe_nutrition_comes_from_food_amounts_and_servings() -> None:
    oats = Food(
        name="Haferflocken",
        base_unit="g",
        calories_kcal=Decimal("370"),
        protein_g=Decimal("13"),
        carbohydrates_g=Decimal("60"),
        fat_g=Decimal("7"),
    )
    milk = Food(
        name="Milch",
        base_unit="ml",
        calories_kcal=Decimal("50"),
        protein_g=Decimal("3.4"),
        carbohydrates_g=Decimal("4.8"),
        fat_g=Decimal("1.5"),
    )
    recipe = Recipe(title="Porridge", servings=2, instructions=["Kochen"])
    recipe.ingredients = [
        RecipeIngredient(amount=Decimal("100"), unit="g", position=0, food=oats),
        RecipeIngredient(amount=Decimal("200"), unit="ml", position=1, food=milk),
    ]

    nutrition = calculate_recipe_nutrition(recipe)

    assert nutrition.total == Nutrients(
        calories_kcal=Decimal("470"),
        protein_g=Decimal("19.8"),
        carbohydrates_g=Decimal("69.6"),
        fat_g=Decimal("10.0"),
    )
    assert nutrition.per_serving == Nutrients(
        calories_kcal=Decimal("235"),
        protein_g=Decimal("9.9"),
        carbohydrates_g=Decimal("34.8"),
        fat_g=Decimal("5.0"),
    )


def test_recipe_nutrition_converts_food_portions_to_base_amounts() -> None:
    egg = Food(
        name="Ei", base_unit="g", calories_kcal=Decimal("140"),
        protein_g=Decimal("13"), carbohydrates_g=Decimal("1"), fat_g=Decimal("9"),
    )
    piece = FoodPortion(name="Stück", amount=Decimal("60"), position=0)
    recipe = Recipe(title="Eier", servings=1, instructions=["Kochen"])
    recipe.ingredients = [
        RecipeIngredient(
            amount=Decimal("2"), unit="g", position=0, food=egg, food_portion=piece
        )
    ]
    assert calculate_recipe_nutrition(recipe).total.calories_kcal == Decimal("168.0")
