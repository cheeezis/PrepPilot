from collections.abc import Iterator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from preppilot_api.database import get_session
from preppilot_api.main import app
from preppilot_api.models import Base


def recipe_payload(title: str = "Kartoffel-Curry") -> dict[str, object]:
    return {
        "title": title,
        "categories": ["lunch", "dinner"],
        "servings": 4,
        "calories_per_serving": 520,
        "protein_per_serving": 32,
        "carbs_per_serving": 61,
        "fat_per_serving": 14,
        "ingredients": [
            {"amount": 800, "unit": "g", "name": "Kartoffeln"},
            {"amount": 1, "unit": "Dose", "name": "Kichererbsen"},
        ],
        "instructions": ["Kartoffeln schneiden.", "Alles köcheln lassen."],
        "preparation_minutes": 15,
        "cooking_minutes": 30,
        "source_url": None,
    }


def test_personal_recipe_can_be_created_edited_and_deleted() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    def override_session() -> Iterator[Session]:
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    try:
        with TestClient(app) as client:
            empty_response = client.get("/api/recipes")
            create_response = client.post("/api/recipes", json=recipe_payload())
            recipe_id = create_response.json()["id"]
            update_response = client.put(
                f"/api/recipes/{recipe_id}",
                json=recipe_payload("Kartoffel-Curry mit Spinat"),
            )
            list_response = client.get("/api/recipes")
            delete_response = client.delete(f"/api/recipes/{recipe_id}")
            final_response = client.get("/api/recipes")
    finally:
        app.dependency_overrides.clear()

    assert empty_response.status_code == 200
    assert empty_response.json() == []
    assert create_response.status_code == 201
    assert create_response.json()["title"] == "Kartoffel-Curry"
    assert create_response.json()["source_url"] is None
    assert update_response.status_code == 200
    assert update_response.json()["title"] == "Kartoffel-Curry mit Spinat"
    assert len(list_response.json()) == 1
    assert delete_response.status_code == 204
    assert final_response.json() == []


def test_personal_recipe_rejects_blank_content() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/recipes",
            json={
                **recipe_payload(),
                "ingredients": [{"amount": 1, "unit": " ", "name": "Salz"}],
            },
        )

    assert response.status_code == 422
