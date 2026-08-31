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
