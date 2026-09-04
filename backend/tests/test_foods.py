from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from preppilot_api.database import get_session
from preppilot_api.main import app
from preppilot_api.models import Base


@pytest.fixture
def client() -> Iterator[TestClient]:
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    def test_session() -> Iterator[Session]:
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = test_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    engine.dispose()


def food_payload(name: str = "Haferflocken") -> dict[str, object]:
    return {
        "name": name,
        "base_unit": "g",
        "calories_kcal": 372.5,
        "protein_g": 13.5,
        "carbohydrates_g": 58.7,
        "fat_g": 7.0,
    }


def test_foods_start_empty_and_can_be_created(client: TestClient) -> None:
    assert client.get("/api/foods").json() == []

    response = client.post("/api/foods", json=food_payload("  Haferflocken  "))

    assert response.status_code == 201
    body = response.json()
    assert body == {
        "id": 1,
        "name": "Haferflocken",
        "base_unit": "g",
        "calories_kcal": 372.5,
        "protein_g": 13.5,
        "carbohydrates_g": 58.7,
        "fat_g": 7.0,
        "created_at": body["created_at"],
        "updated_at": body["updated_at"],
    }
    assert [food["name"] for food in client.get("/api/foods").json()] == [
        "Haferflocken"
    ]


def test_food_can_be_updated_and_deleted(client: TestClient) -> None:
    food_id = client.post("/api/foods", json=food_payload()).json()["id"]
    updated = food_payload("Haferdrink")
    updated["base_unit"] = "ml"

    response = client.put(f"/api/foods/{food_id}", json=updated)

    assert response.status_code == 200
    assert response.json()["name"] == "Haferdrink"
    assert response.json()["base_unit"] == "ml"
    assert client.delete(f"/api/foods/{food_id}").status_code == 204
    assert client.get("/api/foods").json() == []


def test_food_names_are_unique_ignoring_case(client: TestClient) -> None:
    assert client.post("/api/foods", json=food_payload()).status_code == 201

    response = client.post("/api/foods", json=food_payload("haferflocken"))

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Ein Lebensmittel mit diesem Namen existiert bereits"
    )


@pytest.mark.parametrize(
    "changes",
    [
        {"name": "   "},
        {"base_unit": "kg"},
        {"calories_kcal": -1},
        {"protein_g": -1},
        {"carbohydrates_g": -1},
        {"fat_g": -1},
    ],
)
def test_invalid_food_values_are_rejected(
    client: TestClient, changes: dict[str, object]
) -> None:
    payload = food_payload()
    payload.update(changes)

    assert client.post("/api/foods", json=payload).status_code == 422


def test_unknown_food_returns_not_found(client: TestClient) -> None:
    assert client.put("/api/foods/404", json=food_payload()).status_code == 404
    assert client.delete("/api/foods/404").status_code == 404
