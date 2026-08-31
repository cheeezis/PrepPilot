import json
from collections.abc import Iterator
from decimal import Decimal
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from preppilot_api.catalog_data import load_catalog
from preppilot_api.catalog_repository import load_catalog_from_database
from preppilot_api.catalog_seed import replace_catalog
from preppilot_api.database import get_session
from preppilot_api.food_imports import (
    PromoteFoodImportCommand,
    create_food_import,
    promote_food_import,
)
from preppilot_api.food_sources import (
    FoodDataCentralSource,
    get_fooddata_central_source,
)
from preppilot_api.main import app
from preppilot_api.models import Base, Food, FoodImport, FoodImportStatus, FoodOrigin

FIXTURE = Path(__file__).parent / "fixtures/food_imports/fdc_garlic_169230.json"


def test_fdc_adapter_derives_european_carbohydrates() -> None:
    requested: list[tuple[str, float]] = []

    def fetch_json(url: str, timeout: float) -> dict[str, object]:
        requested.append((url, timeout))
        return _payload()

    command = FoodDataCentralSource(
        api_key="test-key",
        base_url="https://example.test/fdc/v1",
        timeout_seconds=4,
        fetch_json=fetch_json,
    ).fetch("169230")

    assert requested == [
        ("https://example.test/fdc/v1/food/169230?api_key=test-key", 4)
    ]
    assert command.candidate_name == "Garlic, raw"
    assert command.calories_per_100 == 149
    assert command.protein_per_100 == Decimal("6.36")
    assert command.carbs_per_100 == Decimal("30.96")
    assert command.fat_per_100 == Decimal("0.5")
    assert not command.review_reasons


def test_fdc_adapter_routes_missing_fiber_to_review() -> None:
    payload = _payload()
    nutrients = payload["foodNutrients"]
    assert isinstance(nutrients, list)
    payload["foodNutrients"] = [
        item
        for item in nutrients
        if isinstance(item, dict) and item.get("nutrient", {}).get("id") != 1079
    ]
    source = FoodDataCentralSource(
        api_key="test-key",
        base_url="https://example.test",
        timeout_seconds=4,
        fetch_json=lambda url, timeout: payload,
    )

    command = source.fetch("169230")

    assert command.carbs_per_100 is None
    assert command.review_reasons == ("missing_fiber",)


def test_fdc_adapter_searches_only_generic_data_types() -> None:
    requested: list[tuple[str, float]] = []

    def fetch_json(url: str, timeout: float) -> dict[str, object]:
        requested.append((url, timeout))
        return {
            "foods": [
                {
                    "fdcId": 170416,
                    "description": "Parsley, fresh",
                    "dataType": "SR Legacy",
                }
            ]
        }

    source = FoodDataCentralSource(
        api_key="test-key",
        base_url="https://example.test/fdc/v1",
        timeout_seconds=4,
        fetch_json=fetch_json,
    )

    candidates = source.search("Parsley", limit=3)

    assert requested == [
        (
            "https://example.test/fdc/v1/foods/search?api_key=test-key&"
            "query=Parsley&dataType=Foundation%2CSR+Legacy&pageSize=3",
            4,
        )
    ]
    assert [(item.external_id, item.name, item.data_type) for item in candidates] == [
        ("170416", "Parsley, fresh", "SR Legacy")
    ]


def test_fdc_import_promotes_idempotently_and_survives_seed() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    source = _source()

    with Session(engine) as session, session.begin():
        replace_catalog(session, load_catalog())
        first, created = create_food_import(session, source.fetch("169230"))
        repeated, repeated_created = create_food_import(session, source.fetch("169230"))
        assert created
        assert not repeated_created
        assert repeated.id == first.id
        assert first.status == FoodImportStatus.READY_FOR_CATALOG_REVIEW

        food, promoted = promote_food_import(
            session,
            first.id,
            PromoteFoodImportCommand(catalog_key="garlic", name="Garlic, raw"),
        )
        repeated_food, repeated_promoted = promote_food_import(
            session,
            first.id,
            PromoteFoodImportCommand(catalog_key="garlic", name="Garlic, raw"),
        )
        assert promoted
        assert not repeated_promoted
        assert repeated_food.id == food.id
        assert food.origin == FoodOrigin.FOOD_IMPORT

        replace_catalog(session, load_catalog())
        session.flush()

    with Session(engine) as session:
        catalog = load_catalog_from_database(session)
        assert len(catalog.foods) == 25
        assert "garlic" in {food.key for food in catalog.foods}
        assert session.scalar(select(func.count()).select_from(FoodImport)) == 1


def test_internal_fdc_api_imports_and_promotes() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine) as session, session.begin():
        replace_catalog(session, load_catalog())

    def override_session() -> Iterator[Session]:
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_fooddata_central_source] = _source
    try:
        with TestClient(app) as client:
            imported = client.post(
                "/api/internal/food-imports/sources/fooddata-central/169230"
            )
            food_import_id = imported.json()["food_import"]["id"]
            promoted = client.post(
                f"/api/internal/food-imports/{food_import_id}/promote",
                json={"catalog_key": "garlic", "name": "Garlic, raw"},
            )

        assert imported.status_code == 201
        assert imported.json()["food_import"]["carbs_per_100"] == "30.9600"
        assert promoted.status_code == 200
        assert promoted.json()["created"]
        with Session(engine) as session:
            food = session.scalar(select(Food).where(Food.catalog_key == "garlic"))
            assert food is not None
            assert food.source_food_import_id == food_import_id
    finally:
        app.dependency_overrides.clear()


def test_internal_api_suggests_and_imports_unknown_food_idempotently() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine) as session, session.begin():
        replace_catalog(session, load_catalog())

    def fetch_json(url: str, timeout: float) -> dict[str, object]:
        if "/foods/search?" in url:
            return {
                "foods": [
                    {
                        "fdcId": 169230,
                        "description": "Garlic, raw",
                        "dataType": "SR Legacy",
                    }
                ]
            }
        return _payload()

    source = FoodDataCentralSource(
        api_key="test-key",
        base_url="https://example.test",
        timeout_seconds=4,
        fetch_json=fetch_json,
    )

    def override_session() -> Iterator[Session]:
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_fooddata_central_source] = lambda: source
    try:
        with TestClient(app) as client:
            recipe = client.post(
                "/api/internal/recipe-imports",
                json={
                    "source_name": "test",
                    "external_id": "garlic-recipe",
                    "payload": {
                        "title": "Garlic dish",
                        "servings": "2",
                        "instructions": "Prepare and cook the garlic thoroughly.",
                        "ingredients": [
                            {
                                "line": "6 g Garlic",
                                "name": "Garlic",
                                "amount": "6",
                                "unit": "g",
                            }
                        ],
                    },
                },
            )
            first = client.post(
                "/api/internal/food-imports/suggestions/from-recipe-inbox",
                params={"limit": 5},
            )
            second = client.post(
                "/api/internal/food-imports/suggestions/from-recipe-inbox",
                params={"limit": 5},
            )

        assert recipe.status_code == 201
        assert first.status_code == 200
        assert first.json()["selected"] == 1
        assert first.json()["created"] == 1
        assert first.json()["suggestions"][0]["selected_fdc_id"] == "169230"
        assert second.status_code == 200
        assert second.json()["selected"] == 1
        assert second.json()["created"] == 0
        with Session(engine) as session:
            assert session.scalar(select(func.count()).select_from(FoodImport)) == 1
            assert session.scalar(select(func.count()).select_from(Food)) == 24
    finally:
        app.dependency_overrides.clear()


def test_internal_api_adds_safe_local_alias_before_fdc_search() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine) as session, session.begin():
        replace_catalog(session, load_catalog())

    def unexpected_fetch(url: str, timeout: float) -> dict[str, object]:
        raise AssertionError("FDC must not be called for a safe local alias")

    source = FoodDataCentralSource(
        api_key="test-key",
        base_url="https://example.test",
        timeout_seconds=4,
        fetch_json=unexpected_fetch,
    )

    def override_session() -> Iterator[Session]:
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_fooddata_central_source] = lambda: source
    try:
        with TestClient(app) as client:
            recipe = client.post(
                "/api/internal/recipe-imports",
                json={
                    "source_name": "test",
                    "external_id": "chickpea-recipe",
                    "payload": {
                        "title": "Chickpea dish",
                        "servings": "2",
                        "instructions": (
                            "Warm the chickpeas in a pan, season them carefully, and "
                            "serve them immediately while they are still hot."
                        ),
                        "ingredients": [
                            {
                                "line": "200 g Chickpeas",
                                "name": "Chickpeas",
                                "amount": "200",
                                "unit": "g",
                            }
                        ],
                    },
                },
            )
            suggestions = client.post(
                "/api/internal/food-imports/suggestions/from-recipe-inbox",
                params={"limit": 5},
            )
            resolved = client.get(
                f"/api/internal/recipe-imports/{recipe.json()['recipe_import']['id']}"
            )

        assert suggestions.status_code == 200
        assert suggestions.json()["local_aliases_added"] == 1
        assert suggestions.json()["suggestions"][0]["status"] == "local_alias_added"
        assert (
            suggestions.json()["suggestions"][0]["local_food_key"]
            == "chickpeas_cooked"
        )
        assert resolved.json()["status"] == "ready_for_catalog_review"
        with Session(engine) as session:
            assert session.scalar(select(func.count()).select_from(FoodImport)) == 0
            assert session.scalar(select(func.count()).select_from(Food)) == 24
    finally:
        app.dependency_overrides.clear()


def _source() -> FoodDataCentralSource:
    return FoodDataCentralSource(
        api_key="test-key",
        base_url="https://example.test",
        timeout_seconds=4,
        fetch_json=lambda url, timeout: _payload(),
    )


def _payload() -> dict[str, object]:
    value = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value
