from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from preppilot_api.models import (
    Base,
    Food,
    FoodPortion,
    Meal,
    MealIngredient,
    MealRole,
    MealRoleAssignment,
    MeasurementUnit,
)
from preppilot_api.recipe_import import RecipeImportOptions, import_themealdb_recipe
from preppilot_api.themealdb import Recipe, RecipeIngredient


class StubRecipeSource:
    def __init__(self, recipe: Recipe) -> None:
        self.recipe = recipe

    def get_recipe(self, meal_id: str) -> Recipe:
        assert meal_id == self.recipe.source_id
        return self.recipe


class StubIngredientResolver:
    def resolve(self, session: Session, source_name: str, external_name: str) -> Food:
        assert source_name == "themealdb"
        food = Food(
            name=external_name,
            brand=None,
            unit=MeasurementUnit.GRAM,
            calories_per_100=Decimal("100"),
            protein_per_100=Decimal("10"),
            carbs_per_100=Decimal("5"),
            fat_per_100=Decimal("2"),
            source_name="test",
            source_reference=external_name,
            source_retrieved_at=datetime.now(UTC),
        )
        session.add(food)
        session.flush()
        portion = _PORTIONS.get(external_name)
        if portion is not None:
            unit, amount, gram_weight, modifier = portion
            session.add(
                FoodPortion(
                    food_id=food.id,
                    amount=amount,
                    unit=unit,
                    modifier=modifier,
                    gram_weight=gram_weight,
                    source_name="test",
                    source_reference=external_name,
                    source_retrieved_at=datetime.now(UTC),
                )
            )
        return food


_PORTIONS: dict[str, tuple[str, Decimal, Decimal, str | None]] = {
    "Olive Oil": ("tbsp", Decimal("1"), Decimal("13.5"), None),
    "Onion": ("piece", Decimal("1"), Decimal("110"), "medium"),
    "Ginger": ("pinch", Decimal("1"), Decimal("0.3"), None),
    "Harissa Spice": ("tbsp", Decimal("1"), Decimal("10"), None),
    "Dried Apricots": ("piece", Decimal("0.5"), Decimal("3.5"), None),
    "Chicken Stock": ("cup", Decimal("1"), Decimal("240"), None),
    "Coriander": ("handful", Decimal("1"), Decimal("10"), None),
}


def test_imports_chicken_couscous_as_one_calculation_portion() -> None:
    recipe = _chicken_couscous_recipe()

    with _session() as session:
        meal = import_themealdb_recipe(
            session,
            meal_id="52850",
            options=RecipeImportOptions(
                source_servings=4,
                preparation_minutes=25,
                role=MealRole.MAIN_MEAL,
            ),
            recipe_source=StubRecipeSource(recipe),
            ingredient_resolver=StubIngredientResolver(),
        )

        assert meal.source_servings == 4
        assert meal.preparation_minutes == 25
        assert session.scalar(select(MealRoleAssignment.role)) == MealRole.MAIN_MEAL

        ingredients = [
            (name, amount, source_measure or "")
            for name, amount, source_measure in session.execute(
                select(Food.name, MealIngredient.amount, MealIngredient.source_measure)
                .join(MealIngredient, MealIngredient.food_id == Food.id)
                .order_by(Food.id)
            ).tuples()
        ]
        assert ingredients == [
            ("Olive Oil", Decimal("3.375"), "1 tbsp"),
            ("Onion", Decimal("27.500"), "1 chopped"),
            ("Chicken Breast", Decimal("50.000"), "200g"),
            ("Ginger", Decimal("0.075"), "pinch"),
            ("Harissa Spice", Decimal("5.000"), "2 tblsp"),
            ("Dried Apricots", Decimal("17.500"), "10"),
            ("Chickpeas", Decimal("55.000"), "220g"),
            ("Couscous", Decimal("50.000"), "200g"),
            ("Chicken Stock", Decimal("50.000"), "200ml"),
            ("Coriander", Decimal("2.500"), "Handful"),
        ]


def test_rolls_back_complete_recipe_when_one_measure_is_unsupported() -> None:
    recipe = Recipe(
        source_id="test",
        name="Broken recipe",
        category=None,
        area=None,
        instructions="Try to cook it.",
        original_source_url=None,
        ingredients=(
            RecipeIngredient(name="Chicken Breast", measure="200g"),
            RecipeIngredient(name="Salt", measure="to taste"),
        ),
    )

    with _session() as session:
        with pytest.raises(ValueError):
            import_themealdb_recipe(
                session,
                meal_id="test",
                options=RecipeImportOptions(
                    source_servings=2,
                    preparation_minutes=10,
                    role=MealRole.MAIN_MEAL,
                ),
                recipe_source=StubRecipeSource(recipe),
                ingredient_resolver=StubIngredientResolver(),
            )

        assert session.scalar(select(func.count()).select_from(Meal)) == 0
        assert session.scalar(select(func.count()).select_from(Food)) == 0


def _session() -> Session:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    return Session(engine)


def _chicken_couscous_recipe() -> Recipe:
    return Recipe(
        source_id="52850",
        name="Chicken Couscous",
        category="Chicken",
        area="Moroccan",
        instructions="Cook everything.",
        original_source_url="https://example.com/original",
        ingredients=(
            RecipeIngredient(name="Olive Oil", measure="1 tbsp"),
            RecipeIngredient(name="Onion", measure="1 chopped"),
            RecipeIngredient(name="Chicken Breast", measure="200g"),
            RecipeIngredient(name="Ginger", measure="pinch"),
            RecipeIngredient(name="Harissa Spice", measure="2 tblsp"),
            RecipeIngredient(name="Dried Apricots", measure="10"),
            RecipeIngredient(name="Chickpeas", measure="220g"),
            RecipeIngredient(name="Couscous", measure="200g"),
            RecipeIngredient(name="Chicken Stock", measure="200ml"),
            RecipeIngredient(name="Coriander", measure="Handful"),
        ),
    )
