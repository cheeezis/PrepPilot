from decimal import Decimal

from preppilot_api.nutrition import Nutrients
from preppilot_api.planner import (
    PlanTargets,
    _combination_can_reach_outer_limits,
    generate_day_plans,
)
from preppilot_api.recipe_repository import (
    RecipeCategory,
    RecipeDefinition,
    RecipeIngredient,
)


def recipe(
    recipe_id: int,
    category: RecipeCategory,
    values: tuple[str, str, str, str],
) -> RecipeDefinition:
    return RecipeDefinition(
        id=recipe_id,
        title=f"Recipe {recipe_id}",
        categories=(category,),
        servings=4,
        source_url=f"https://example.test/{recipe_id}",
        ingredients=(RecipeIngredient(Decimal("1"), "Stück", "Testzutat"),),
        instructions=("instruction",),
        preparation_minutes=10,
        cooking_minutes=20,
        nutrients=Nutrients(*(Decimal(value) for value in values)),
    )


RECIPES = (
    recipe(1, "breakfast", ("525", "52", "48", "15.5")),
    recipe(2, "breakfast", ("409", "26.5", "61", "9")),
    recipe(3, "breakfast", ("404", "36", "54", "6.5")),
    recipe(4, "lunch", ("384", "42", "48", "4")),
    recipe(5, "lunch", ("295", "21", "45", "5")),
    recipe(6, "lunch", ("384", "22", "67", "3.5")),
    recipe(7, "dinner", ("363", "25.5", "49.7", "5.3")),
    recipe(8, "dinner", ("465", "34.2", "45.9", "13.8")),
    recipe(9, "dinner", ("255", "17", "19", "13")),
    recipe(10, "dinner", ("296", "21.5", "30.8", "7.2")),
)


def targets() -> PlanTargets:
    return PlanTargets(Decimal(1350), Decimal(120), Decimal(40), Decimal(140))


def test_reference_profile_returns_recipe_first_plan() -> None:
    plans = generate_day_plans(targets(), RECIPES)
    assert plans and plans[0].status == "valid"
    assert len(plans[0].recipes) == 3
    assert all(item.nutrients == item.recipe.nutrients for item in plans[0].recipes)
    assert [item.category for item in plans[0].recipes] == [
        "breakfast",
        "lunch",
        "dinner",
    ]


def test_plan_generation_is_reproducible() -> None:
    assert generate_day_plans(targets(), RECIPES) == generate_day_plans(
        targets(), RECIPES
    )


def test_requires_one_recipe_from_each_main_meal_category() -> None:
    recipes_without_lunch = tuple(
        candidate for candidate in RECIPES if "lunch" not in candidate.categories
    )

    assert generate_day_plans(targets(), recipes_without_lunch) == ()


def test_can_add_an_optional_snack_slot() -> None:
    recipes = RECIPES + (
        recipe(11, "snack", ("250", "20", "25", "7")),
    )

    plans = generate_day_plans(
        PlanTargets(Decimal(1600), Decimal(140), Decimal(47), Decimal(165)),
        recipes,
        ("breakfast", "lunch", "dinner", "snack"),
    )

    assert plans
    assert [item.category for item in plans[0].recipes] == [
        "breakfast",
        "lunch",
        "dinner",
        "snack",
    ]


def test_can_use_one_batch_for_lunch_and_dinner() -> None:
    shared = RecipeDefinition(
        **{
            **recipe(11, "lunch", ("600", "50", "60", "15")).__dict__,
            "categories": ("lunch", "dinner"),
        }
    )

    plans = generate_day_plans(
        PlanTargets(Decimal(1200), Decimal(100), Decimal(30), Decimal(120)),
        (shared,),
        ("lunch", "dinner"),
    )

    assert plans
    assert [item.recipe.id for item in plans[0].recipes] == [11, 11]


def test_skips_recipe_combinations_that_cannot_reach_outer_limits() -> None:
    recipes = tuple(
        recipe(recipe_id, "dinner", ("100", "5", "10", "2"))
        for recipe_id in range(1, 4)
    )
    high_targets = PlanTargets(
        calories=Decimal("2500"),
        protein_minimum=Decimal("220"),
        fat_maximum=Decimal("71"),
        carbs=Decimal("233"),
    )

    assert not _combination_can_reach_outer_limits(recipes, high_targets)


def test_api_serializes_recipe_source_data(monkeypatch) -> None:
    from fastapi.testclient import TestClient

    import preppilot_api.main as main_module

    monkeypatch.setattr(main_module, "load_recipes", lambda session: RECIPES)
    with TestClient(main_module.app) as client:
        response = client.post(
            "/api/day-plans",
            json={
                "calories": 1350,
                "protein_minimum": 120,
                "fat_maximum": 40,
                "carbs": 140,
                "meal_categories": ["breakfast", "lunch", "dinner", "snack"],
            },
        )
    assert response.status_code == 200
    assert response.json()["plans"] == []


def test_api_serializes_a_single_portion_per_meal(monkeypatch) -> None:
    from fastapi.testclient import TestClient

    import preppilot_api.main as main_module

    monkeypatch.setattr(main_module, "load_recipes", lambda session: RECIPES)
    with TestClient(main_module.app) as client:
        response = client.post(
            "/api/day-plans",
            json={
                "calories": 1350,
                "protein_minimum": 120,
                "fat_maximum": 40,
                "carbs": 140,
            },
        )
    assert response.status_code == 200
    planned = response.json()["plans"][0]["recipes"][0]
    assert planned["category"] == "breakfast"
    assert planned["source_url"].startswith("https://")
    assert planned["ingredients"] == [
        {"amount": 1.0, "unit": "Stück", "name": "Testzutat"}
    ]
    assert "portions" not in planned


def test_recipe_api_exposes_the_stored_inventory(monkeypatch) -> None:
    from fastapi.testclient import TestClient

    import preppilot_api.main as main_module

    monkeypatch.setattr(main_module, "load_recipes", lambda session: RECIPES)
    with TestClient(main_module.app) as client:
        response = client.get("/api/recipes")
    assert response.status_code == 200
    assert len(response.json()) == 10
    assert response.json()[0]["ingredients"] == [
        {"amount": 1.0, "unit": "Stück", "name": "Testzutat"}
    ]
    assert response.json()[0]["instructions"] == ["instruction"]
    assert response.json()[0]["servings"] == 4
    assert response.json()[0]["categories"] == ["breakfast"]
    assert response.json()[0]["preparation_minutes"] == 10
