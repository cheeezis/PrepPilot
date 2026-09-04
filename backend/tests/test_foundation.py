from fastapi.testclient import TestClient

from preppilot_api.main import app
from preppilot_api.models import Base


def test_v5_schema_contains_foods_and_relational_recipes() -> None:
    assert set(Base.metadata.tables) == {
        "foods",
        "meal_assignments",
        "recipe_ingredients",
        "recipe_meal_roles",
        "recipes",
        "weekly_plans",
    }


def test_food_catalog_is_the_only_domain_api() -> None:
    with TestClient(app) as client:
        schema = client.get("/openapi.json").json()

    assert set(schema["paths"]) == {
        "/api/foods",
        "/api/foods/{food_id}",
        "/api/health",
        "/api/recipes",
        "/api/recipes/{recipe_id}",
    }
