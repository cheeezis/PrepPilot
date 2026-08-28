from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from preppilot_api.catalog_data import load_catalog
from preppilot_api.main import app
from preppilot_api.planner import PlanTargets, generate_day_plans


@pytest.mark.parametrize(
    ("meal_count", "minimum_valid_plans"), ((3, 2), (4, 3), (5, 3), (6, 3))
)
def test_reference_profile_returns_ranked_plans(
    meal_count: int, minimum_valid_plans: int
) -> None:
    targets = PlanTargets(
        calories=Decimal(2500),
        protein_minimum=Decimal(220),
        fat_maximum=Decimal(71),
        carbs=Decimal(233),
        meal_count=meal_count,
    )

    plans = generate_day_plans(targets, load_catalog())

    assert len(plans) == 3
    assert sum(plan.status == "valid" for plan in plans) >= minimum_valid_plans
    assert [plan.status for plan in plans] == sorted(
        (plan.status for plan in plans), key=lambda status: status != "valid"
    )
    assert all(len(plan.meals) == meal_count for plan in plans)
    assert len({plan.stable_key for plan in plans}) == len(plans)
    assert all(
        len({meal.meal.key for meal in plan.meals}) == len(plan.meals)
        for plan in plans
    )


def test_plan_generation_is_reproducible() -> None:
    targets = PlanTargets(
        calories=Decimal(2500),
        protein_minimum=Decimal(220),
        fat_maximum=Decimal(71),
        carbs=Decimal(233),
        meal_count=5,
    )
    catalog = load_catalog()

    first_result = generate_day_plans(targets, catalog)
    second_result = generate_day_plans(targets, catalog)

    assert first_result == second_result


def test_api_returns_scaled_ingredients_and_rule_evaluations() -> None:
    with TestClient(app) as client:
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
    value = response.json()
    assert value["outcome"] == "plans_found"
    assert len(value["plans"]) == 3
    assert len(value["plans"][0]["evaluations"]) == 4
    assert len(value["plans"][0]["meals"]) == 5
    assert value["plans"][0]["meals"][0]["ingredients"][0]["amount"] > 0


def test_api_labels_approximations_instead_of_presenting_them_as_valid() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/day-plans",
            json={
                "calories": 1800,
                "protein_minimum": 160,
                "fat_maximum": 71,
                "carbs": 233,
                "meal_count": 3,
            },
        )

    assert response.status_code == 200
    value = response.json()
    assert value["outcome"] == "approximations_only"
    assert value["plans"]
    assert all(plan["status"] == "approximation" for plan in value["plans"])
    assert all(
        any(
            evaluation["kind"] == "hard" and not evaluation["satisfied"]
            for evaluation in plan["evaluations"]
        )
        for plan in value["plans"]
    )


def test_api_reports_when_no_candidate_is_within_outer_limits() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/day-plans",
            json={
                "calories": 10000,
                "protein_minimum": 220,
                "fat_maximum": 71,
                "carbs": 233,
                "meal_count": 3,
            },
        )

    assert response.status_code == 200
    assert response.json() == {"outcome": "no_usable_plan", "plans": []}


@pytest.mark.parametrize(
    ("field", "value"),
    (("calories", 0), ("protein_minimum", 0), ("meal_count", 2), ("meal_count", 7)),
)
def test_api_rejects_unsupported_targets(field: str, value: int) -> None:
    request = {
        "calories": 2500,
        "protein_minimum": 220,
        "fat_maximum": 71,
        "carbs": 233,
        "meal_count": 5,
    }
    request[field] = value

    with TestClient(app) as client:
        response = client.post("/api/day-plans", json=request)

    assert response.status_code == 422
