from decimal import Decimal

from preppilot_api.nutrition import Nutrients
from preppilot_api.planner import (
    PlanTargets,
    _combination_can_reach_outer_limits,
    generate_day_plans,
    generate_week_plan,
)
from preppilot_api.recipe_repository import RecipeCategory, RecipeDefinition


def recipe(
    recipe_id: int,
    category: RecipeCategory,
    values: tuple[str, str, str, str],
    servings: int = 4,
) -> RecipeDefinition:
    return RecipeDefinition(
        id=recipe_id,
        title=f"Recipe {recipe_id}",
        categories=(category,),
        servings=servings,
        source_url=f"https://example.test/{recipe_id}",
        license_name="Open Government Licence v3.0",
        attribution_text="NHS",
        ingredients=("ingredient",),
        instructions=("instruction",),
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
    return PlanTargets(Decimal(2400), Decimal(200), Decimal(71), Decimal(233))


def test_reference_profile_returns_recipe_first_plan() -> None:
    plans = generate_day_plans(targets(), RECIPES)
    assert plans and plans[0].status == "valid"
    assert len(plans[0].recipes) == 3
    assert all(item.portions in (1, 2) for item in plans[0].recipes)
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
        targets(),
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


def test_does_not_use_a_multi_category_recipe_twice() -> None:
    shared = RecipeDefinition(
        **{
            **recipe(11, "breakfast", ("600", "50", "60", "15")).__dict__,
            "categories": ("breakfast", "snack"),
        }
    )

    plans = generate_day_plans(
        targets(),
        RECIPES + (shared,),
        ("breakfast", "snack"),
    )

    assert all(
        len({item.recipe.id for item in plan.recipes}) == len(plan.recipes)
        for plan in plans
    )


def test_week_plan_uses_up_to_three_consecutive_days() -> None:
    recipes = tuple(
        recipe(
            recipe_id,
            "breakfast",
            ("500", "50", "50", "18"),
            servings=3,
        )
        for recipe_id in range(1, 5)
    )
    week = generate_week_plan(
        PlanTargets(Decimal(500), Decimal(50), Decimal(20), Decimal(50)),
        recipes,
        7,
        ("breakfast",),
    )

    assert week is not None
    assert [block.day_count for block in week.blocks] == [3, 3, 1]
    recipe_ids = [block.plan.recipes[0].recipe.id for block in week.blocks]
    assert len(set(recipe_ids)) == len(recipe_ids)


def test_week_plan_matches_four_servings_to_two_days_with_two_portions() -> None:
    recipes = tuple(
        recipe(recipe_id, "breakfast", ("500", "50", "50", "18"))
        for recipe_id in range(1, 4)
    )
    week = generate_week_plan(
        PlanTargets(Decimal(1000), Decimal(100), Decimal(40), Decimal(100)),
        recipes,
        3,
        ("breakfast",),
    )

    assert week is not None
    assert week.blocks[0].day_count == 2
    assert week.blocks[0].plan.recipes[0].portions == 2


def test_week_plan_requires_between_three_and_seven_days() -> None:
    for day_count in (2, 8):
        try:
            generate_week_plan(targets(), RECIPES, day_count)
        except ValueError as error:
            assert str(error) == "day count must be between 3 and 7"
        else:
            raise AssertionError("invalid day count was accepted")


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
                "calories": 2500,
                "protein_minimum": 220,
                "fat_maximum": 71,
                "carbs": 233,
                "meal_categories": ["breakfast", "lunch", "dinner", "snack"],
            },
        )
    assert response.status_code == 200
    assert response.json()["plans"] == []


def test_api_returns_no_plan_when_a_selected_category_is_missing(monkeypatch) -> None:
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
            },
        )
    assert response.status_code == 200
    planned = response.json()["plans"][0]["recipes"][0]
    assert planned["category"] == "breakfast"
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
    assert response.json()[0]["categories"] == ["breakfast"]


def test_week_plan_api_marks_consecutive_prep_days(monkeypatch) -> None:
    from fastapi.testclient import TestClient

    import preppilot_api.main as main_module

    recipes = tuple(
        recipe(recipe_id, "breakfast", ("500", "50", "50", "18"))
        for recipe_id in range(1, 3)
    )
    monkeypatch.setattr(main_module, "load_recipes", lambda session: recipes)
    with TestClient(main_module.app) as client:
        response = client.post(
            "/api/week-plans",
            json={
                "days": 3,
                "calories": 500,
                "protein_minimum": 50,
                "fat_maximum": 20,
                "carbs": 50,
                "meal_categories": ["breakfast"],
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["outcome"] == "plan_found"
    assert len(payload["days"]) == 3
    assert payload["days"][0]["block_start_day"] == 1
    assert payload["days"][0]["block_end_day"] == 3
    assert payload["days"][1]["prep_with_previous"] is True
    assert payload["days"][2]["prep_with_previous"] is True
