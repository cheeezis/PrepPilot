import json
from collections.abc import Iterator
from decimal import Decimal
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from preppilot_api.catalog_data import load_catalog
from preppilot_api.catalog_seed import replace_catalog
from preppilot_api.database import get_session
from preppilot_api.main import app
from preppilot_api.models import (
    Base,
    FoodAlias,
    FoodMeasureDefault,
    ImportReviewDecision,
    Meal,
    RecipeImport,
    RecipeImportStatus,
    ReviewDecisionAction,
)
from preppilot_api.recipe_imports import (
    CreateRecipeImportCommand,
    ReviewDecisionCommand,
    apply_review_decision,
    create_recipe_import,
    ingredients_for_import,
)

FIXTURES = Path(__file__).parent / "fixtures" / "recipe_imports"


@pytest.fixture
def session() -> Iterator[Session]:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as database_session, database_session.begin():
        replace_catalog(database_session, load_catalog())
    with Session(engine) as database_session:
        yield database_session


def test_normalizes_two_versioned_metric_recipe_examples(session: Session) -> None:
    first, first_created = create_recipe_import(
        session, _command("metric_chicken_rice.json")
    )
    second, second_created = create_recipe_import(
        session, _command("metric_whey_shake.json")
    )

    assert first_created and second_created
    assert first.status == RecipeImportStatus.READY_FOR_CATALOG_REVIEW
    assert second.status == RecipeImportStatus.READY_FOR_CATALOG_REVIEW
    assert [
        ingredient.normalized_amount
        for ingredient in ingredients_for_import(session, first.id)
    ] == [200, 100, 150, 15]
    assert [
        ingredient.normalized_amount
        for ingredient in ingredients_for_import(session, second.id)
    ] == [500, 45]
    assert session.scalar(select(func.count()).select_from(Meal)) == 10


def test_keeps_raw_payload_and_imports_idempotently(session: Session) -> None:
    command = _command("metric_chicken_rice.json")
    first, first_created = create_recipe_import(session, command)
    second, second_created = create_recipe_import(session, command)

    assert first_created
    assert not second_created
    assert first.id == second.id
    assert first.raw_payload == command.payload.model_dump(mode="json")
    assert session.scalar(select(func.count()).select_from(RecipeImport)) == 1


@pytest.mark.parametrize(
    ("fixture_name", "reason"),
    (
        ("unknown_food.json", "unknown_food"),
        ("missing_measure.json", "missing_measure_default"),
    ),
)
def test_routes_incomplete_imports_to_review(
    session: Session, fixture_name: str, reason: str
) -> None:
    recipe_import, _ = create_recipe_import(session, _command(fixture_name))

    ingredient = ingredients_for_import(session, recipe_import.id)[0]
    assert recipe_import.status == RecipeImportStatus.NEEDS_REVIEW
    assert ingredient.review_reason is not None
    assert ingredient.review_reason.value == reason


def test_reusable_alias_reprocesses_unknown_food(session: Session) -> None:
    recipe_import, _ = create_recipe_import(session, _command("unknown_food.json"))
    ingredient = ingredients_for_import(session, recipe_import.id)[0]

    apply_review_decision(
        session,
        recipe_import.id,
        ReviewDecisionCommand(
            action=ReviewDecisionAction.ADD_ALIAS,
            ingredient_id=ingredient.id,
            food_key="chicken_breast",
        ),
    )

    assert recipe_import.status == RecipeImportStatus.READY_FOR_CATALOG_REVIEW
    assert session.scalar(select(func.count()).select_from(FoodAlias)) == 1
    assert session.scalar(select(func.count()).select_from(ImportReviewDecision)) == 1

    replace_catalog(session, load_catalog())
    session.flush()

    assert recipe_import.status == RecipeImportStatus.READY_FOR_CATALOG_REVIEW
    assert session.scalar(select(func.count()).select_from(FoodAlias)) == 1


def test_measure_default_reprocesses_piece_quantity(session: Session) -> None:
    recipe_import, _ = create_recipe_import(session, _command("missing_measure.json"))
    ingredient = ingredients_for_import(session, recipe_import.id)[0]

    apply_review_decision(
        session,
        recipe_import.id,
        ReviewDecisionCommand(
            action=ReviewDecisionAction.ADD_MEASURE_DEFAULT,
            ingredient_id=ingredient.id,
            food_key="egg",
            amount=Decimal(50),
            source_name="FoodData Central test reference",
        ),
    )

    normalized = ingredients_for_import(session, recipe_import.id)[0]
    assert recipe_import.status == RecipeImportStatus.READY_FOR_CATALOG_REVIEW
    assert normalized.normalized_amount == 100
    assert session.scalar(select(func.count()).select_from(FoodMeasureDefault)) == 1


def test_internal_api_exposes_queue_and_applies_override() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine) as seed_session, seed_session.begin():
        replace_catalog(seed_session, load_catalog())

    def override_session() -> Iterator[Session]:
        with Session(engine) as api_session:
            yield api_session

    app.dependency_overrides[get_session] = override_session
    try:
        with TestClient(app) as client:
            created = client.post(
                "/api/internal/recipe-imports",
                json=_fixture_value("unknown_food.json"),
            )
            assert created.status_code == 201
            value = created.json()["recipe_import"]
            assert value["status"] == "needs_review"
            recipe_import_id = value["id"]
            ingredient_id = value["ingredients"][0]["id"]

            queue = client.get(
                "/api/internal/recipe-imports",
                params={"import_status": "needs_review"},
            )
            assert [item["id"] for item in queue.json()] == [recipe_import_id]

            resolved = client.post(
                f"/api/internal/recipe-imports/{recipe_import_id}/decisions",
                json={
                    "action": "override_amount",
                    "ingredient_id": ingredient_id,
                    "food_key": "chicken_breast",
                    "amount": 200,
                },
            )
            assert resolved.status_code == 200
            assert resolved.json()["status"] == "ready_for_catalog_review"
            assert resolved.json()["ingredients"][0]["normalized_amount"] == 200

            promotion = {
                "catalog_key": "imported_chicken",
                "name": "Imported chicken",
                "preparation_minutes": 10,
                "instructions": "Cook the chicken.",
                "roles": ["main_meal"],
                "portion_factors": [1, 1.5],
            }
            promoted = client.post(
                f"/api/internal/recipe-imports/{recipe_import_id}/promote",
                json=promotion,
            )
            assert promoted.status_code == 200
            assert promoted.json()["created"]
            repeated = client.post(
                f"/api/internal/recipe-imports/{recipe_import_id}/promote",
                json=promotion,
            )
            assert repeated.status_code == 200
            assert not repeated.json()["created"]
    finally:
        app.dependency_overrides.clear()


def _command(name: str) -> CreateRecipeImportCommand:
    return CreateRecipeImportCommand.model_validate(_fixture_value(name))


def _fixture_value(name: str) -> dict[str, object]:
    value = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value
