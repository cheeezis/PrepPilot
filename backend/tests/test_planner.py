from decimal import Decimal

from preppilot_api.nutrition import Nutrients
from preppilot_api.planner import (
    PlanTargets,
    _combination_can_reach_outer_limits,
    generate_day_plans,
)
from preppilot_api.recipe_repository import RecipeDefinition


def recipe(recipe_id: int, values: tuple[str, str, str, str]) -> RecipeDefinition:
    return RecipeDefinition(
        id=recipe_id,
        title=f"Recipe {recipe_id}",
        category="dinner",
        servings=4,
        source_url=f"https://example.test/{recipe_id}",
        license_name="Open Government Licence v3.0",
        attribution_text="NHS",
        ingredients=("ingredient",),
        instructions=("instruction",),
        nutrients=Nutrients(*(Decimal(value) for value in values)),
    )


RECIPES = (
    recipe(1, ("525", "52", "48", "15.5")),
    recipe(2, ("409", "26.5", "61", "9")),
    recipe(3, ("404", "36", "54", "6.5")),
    recipe(4, ("384", "42", "48", "4")),
    recipe(5, ("295", "21", "45", "5")),
    recipe(6, ("384", "22", "67", "3.5")),
    recipe(7, ("363", "25.5", "49.7", "5.3")),
    recipe(8, ("465", "34.2", "45.9", "13.8")),
    recipe(9, ("255", "17", "19", "13")),
    recipe(10, ("296", "21.5", "30.8", "7.2")),
)


def targets() -> PlanTargets:
    return PlanTargets(Decimal(2500), Decimal(220), Decimal(71), Decimal(233), 5)


def test_reference_profile_returns_recipe_first_plan() -> None:
    plans = generate_day_plans(targets(), RECIPES)
    assert plans and plans[0].status == "valid"
    assert len(plans[0].recipes) == 5
    assert all(item.portions in (1, 2) for item in plans[0].recipes)
    assert len({item.recipe.id for item in plans[0].recipes}) == 5


def test_plan_generation_is_reproducible() -> None:
    assert generate_day_plans(targets(), RECIPES) == generate_day_plans(
        targets(), RECIPES
    )


def test_skips_recipe_combinations_that_cannot_reach_outer_limits() -> None:
    recipes = tuple(
        recipe(recipe_id, ("100", "5", "10", "2"))
        for recipe_id in range(1, 4)
    )
    high_targets = PlanTargets(
        calories=Decimal("2500"),
        protein_minimum=Decimal("220"),
        fat_maximum=Decimal("71"),
        carbs=Decimal("233"),
        meal_count=3,
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
                "calories": 2500,
                "protein_minimum": 220,
                "fat_maximum": 71,
                "carbs": 233,
                "meal_count": 5,
            },
        )
    assert response.status_code == 200
    planned = response.json()["plans"][0]["recipes"][0]
    assert planned["category"] == "dinner"
    assert planned["source_url"].startswith("https://")
    assert planned["ingredients"] == ["ingredient"]
    assert planned["portions"] in (1, 2)


def test_recipe_api_exposes_the_stored_inventory(monkeypatch) -> None:
    from fastapi.testclient import TestClient

    import preppilot_api.main as main_module

    monkeypatch.setattr(main_module, "load_recipes", lambda session: RECIPES)
    with TestClient(main_module.app) as client:
        response = client.get("/api/recipes")
    assert response.status_code == 200
    assert len(response.json()) == 10
    assert response.json()[0]["ingredients"] == ["ingredient"]
    assert response.json()[0]["instructions"] == ["instruction"]
    assert response.json()[0]["servings"] == 4
    assert response.json()[0]["category"] == "dinner"
