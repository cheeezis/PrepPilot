from fastapi.testclient import TestClient

from preppilot_api.main import app
from preppilot_api.models import Base


def test_v5_schema_contains_only_the_food_catalog() -> None:
    assert set(Base.metadata.tables) == {"foods"}


def test_food_catalog_is_the_only_domain_api() -> None:
    with TestClient(app) as client:
        schema = client.get("/openapi.json").json()

    assert set(schema["paths"]) == {
        "/api/foods",
        "/api/foods/{food_id}",
        "/api/health",
    }
