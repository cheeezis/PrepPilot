from collections import Counter
from decimal import Decimal
from itertools import product

import pytest
from pydantic import ValidationError

from preppilot_api.catalog_data import load_catalog, parse_catalog
from preppilot_api.models import MealRole
from preppilot_api.nutrition import Nutrients, calculate_meal_nutrients


def test_loads_complete_versioned_catalog() -> None:
    catalog = load_catalog()

    assert len(catalog.foods) == 24
    assert len(catalog.meals) == 10
    assert {food.unit.value for food in catalog.foods} == {"g", "ml"}


def test_catalog_contains_reviewed_import_normalization_metadata() -> None:
    catalog = load_catalog()
    foods = {food.key: food for food in catalog.foods}

    assert foods["egg"].aliases == ("Egg", "Eggs")
    assert foods["egg"].measure_defaults[0].key == "medium"
    assert foods["banana"].measure_defaults[0].amount == 136
    assert foods["vegetable_oil"].aliases == ("Oil",)


def test_food_profiles_reference_general_food_concepts() -> None:
    catalog = load_catalog()
    foods = {food.key: food for food in catalog.foods}

    assert foods["milk_1_5"].concept_key == "milk"
    assert foods["milk_1_5"].concept_name == "Milk"
    assert foods["rice_dry"].concept_key == "long_grain_rice"
    assert foods["rice_dry"].concept_name == "Long-grain rice"


def test_every_food_has_a_reviewed_traceable_source() -> None:
    catalog = load_catalog()

    for food in catalog.foods:
        assert food.source_name != "preppilot_estimate", food.key
        assert food.source_reference, food.key


def test_catalog_has_two_meals_for_every_role() -> None:
    catalog = load_catalog()
    role_counts = Counter(role for meal in catalog.meals for role in meal.roles)

    assert role_counts == Counter({role: 2 for role in MealRole})


def test_quick_lunches_respect_the_time_limit() -> None:
    catalog = load_catalog()

    quick_lunches = [
        meal for meal in catalog.meals if MealRole.QUICK_LUNCH in meal.roles
    ]
    assert all(meal.preparation_minutes <= 15 for meal in quick_lunches)


def test_catalog_supports_two_valid_plans_for_each_reference_structure() -> None:
    catalog = load_catalog()
    foods = {food.key: food for food in catalog.foods}
    options = {
        role: tuple(
            calculate_meal_nutrients(meal, foods).scaled(factor)
            for meal in catalog.meals
            if role in meal.roles
            for factor in meal.portion_factors
        )
        for role in MealRole
    }
    structures = (
        (MealRole.FIRST_MEAL, MealRole.QUICK_LUNCH, MealRole.MAIN_MEAL),
        (
            MealRole.FIRST_MEAL,
            MealRole.QUICK_LUNCH,
            MealRole.PROTEIN_SNACK,
            MealRole.MAIN_MEAL,
        ),
        (
            MealRole.FIRST_MEAL,
            MealRole.QUICK_LUNCH,
            MealRole.PROTEIN_SNACK,
            MealRole.PROTEIN_SNACK,
            MealRole.MAIN_MEAL,
        ),
        (
            MealRole.FIRST_MEAL,
            MealRole.QUICK_LUNCH,
            MealRole.PROTEIN_SNACK,
            MealRole.PROTEIN_SNACK,
            MealRole.MAIN_MEAL,
            MealRole.LATE_SNACK,
        ),
    )

    for structure in structures:
        valid_plans = 0
        for combination in product(*(options[role] for role in structure)):
            total = sum(combination, start=Nutrients())
            if (
                Decimal(2375) <= total.calories <= Decimal(2625)
                and total.protein >= 220
                and Decimal("56.8") <= total.fat <= 71
            ):
                valid_plans += 1
                if valid_plans == 2:
                    break
        assert valid_plans == 2, structure


def test_rejects_meal_with_unknown_food() -> None:
    value = """
    {
      "foods": [
        {
          "key": "known",
          "name": "Known food",
          "concept_key": "known",
          "concept_name": "Known food",
          "unit": "g",
          "calories_per_100": 1,
          "protein_per_100": 1,
          "carbs_per_100": 1,
          "fat_per_100": 1,
          "source_name": "test"
        }
      ],
      "meals": [
        {
          "key": "broken",
          "name": "Broken meal",
          "preparation_minutes": 1,
          "instructions": "Test.",
          "roles": ["main_meal"],
          "portion_factors": [1],
          "ingredients": [{"food_key": "missing", "amount": 1}]
        }
      ]
    }
    """

    with pytest.raises(ValidationError, match="unknown foods: missing"):
        parse_catalog(value)
