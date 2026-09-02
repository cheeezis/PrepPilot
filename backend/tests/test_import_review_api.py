from collections.abc import Iterator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from preppilot_api.catalog_data import load_catalog
from preppilot_api.catalog_seed import replace_catalog
from preppilot_api.database import get_session
from preppilot_api.main import app
from preppilot_api.models import Base
from preppilot_api.recipe_imports import CreateRecipeImportCommand, create_recipe_import


def test_lists_and_resolves_one_identity_for_multiple_recipes() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        replace_catalog(session, load_catalog())
        create_recipe_import(session, _command("recipe-1"))
        create_recipe_import(session, _command("recipe-2"))
        session.commit()

        def override_session() -> Iterator[Session]:
            yield session

        app.dependency_overrides[get_session] = override_session
        try:
            with TestClient(app) as client:
                overview = client.get("/api/internal/import-review")
                identifier_id = overview.json()["open_identities"][0]["id"]
                resolved = client.post(
                    f"/api/internal/import-review/food-identities/{identifier_id}/resolve",
                    json={"concept_key": "tomato"},
                )
        finally:
            app.dependency_overrides.pop(get_session, None)

    assert overview.status_code == 200
    assert overview.json()["summary"] == {
        "recipe_count": 2,
        "open_identity_count": 1,
        "review_ingredient_count": 2,
    }
    assert overview.json()["open_identities"][0]["recipe_count"] == 2
    assert resolved.status_code == 200
    assert resolved.json()["summary"] == {
        "recipe_count": 2,
        "open_identity_count": 0,
        "review_ingredient_count": 0,
    }
    assert {recipe["status"] for recipe in resolved.json()["recipes"]} == {
        "ready_for_catalog_review"
    }


def _command(external_id: str) -> CreateRecipeImportCommand:
    return CreateRecipeImportCommand.model_validate(
        {
            "source_name": "wikibooks",
            "external_id": external_id,
            "payload": {
                "title": external_id,
                "servings": "2",
                "instructions": "Prepare the recipe.",
                "ingredients": [
                    {
                        "line": "200 g tomato",
                        "name": "source label",
                        "amount": "200",
                        "unit": "g",
                        "identity": {
                            "source_name": "wikibooks",
                            "external_id": "12345",
                            "source_label": "Cookbook:Tomato",
                        },
                    }
                ],
            },
        }
    )
