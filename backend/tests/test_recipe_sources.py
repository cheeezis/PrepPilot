import json
from collections.abc import Iterator
from pathlib import Path
from urllib.error import URLError

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from preppilot_api import recipe_sources
from preppilot_api.catalog_data import load_catalog
from preppilot_api.catalog_seed import replace_catalog
from preppilot_api.database import get_session
from preppilot_api.main import app
from preppilot_api.models import RecipeImport
from preppilot_api.recipe_sources import (
    RecipeSourceNotFoundError,
    RecipeSourcePayloadError,
    RecipeSourceUnavailableError,
    TheMealDbSource,
    get_themealdb_source,
)

FIXTURE = Path(__file__).parent / "fixtures/recipe_imports/themealdb_arrabiata.json"


def test_themealdb_adapter_maps_recipe_and_preserves_source_payload() -> None:
    source_payload = _source_payload()
    requested: list[tuple[str, float]] = []

    def fetch_json(url: str, timeout: float) -> dict[str, object]:
        requested.append((url, timeout))
        return {"meals": [source_payload]}

    fetched = TheMealDbSource(
        api_key="1",
        base_url="https://example.test/api/json/v1",
        timeout_seconds=3,
        fetch_json=fetch_json,
    ).fetch("52771")

    assert requested == [("https://example.test/api/json/v1/1/lookup.php?i=52771", 3)]
    assert fetched.source_payload == source_payload
    assert fetched.command.source_name == "themealdb"
    assert fetched.command.external_id == "52771"
    assert fetched.command.payload.title == "Spicy Arrabiata Penne"
    assert fetched.command.payload.servings is None
    assert len(fetched.command.payload.ingredients) == 8
    assert fetched.command.payload.ingredients[0].amount == "1"
    assert fetched.command.payload.ingredients[0].unit == "pound"
    assert fetched.command.payload.ingredients[1].amount == "0.25"
    assert fetched.command.payload.ingredients[1].unit == "cup"
    assert fetched.command.payload.ingredients[7].amount == "sprinkling"
    assert fetched.command.payload.ingredients[7].unit is None


def test_themealdb_adapter_reports_missing_recipe() -> None:
    source = TheMealDbSource(
        api_key="1",
        base_url="https://example.test",
        timeout_seconds=3,
        fetch_json=lambda url, timeout: {"meals": None},
    )

    with pytest.raises(RecipeSourceNotFoundError):
        source.fetch("999999")


def test_themealdb_adapter_discovers_category_with_limit() -> None:
    requested: list[tuple[str, float]] = []

    def fetch_json(url: str, timeout: float) -> dict[str, object]:
        requested.append((url, timeout))
        return {
            "meals": [
                {"idMeal": "100", "strMeal": "First meal"},
                {"idMeal": "100", "strMeal": "Duplicate"},
                {"idMeal": "101", "strMeal": "Second meal"},
                {"idMeal": "102", "strMeal": "Beyond limit"},
            ]
        }

    source = TheMealDbSource(
        api_key="1",
        base_url="https://example.test/api/json/v1",
        timeout_seconds=3,
        fetch_json=fetch_json,
    )

    references = source.discover_category("Quick Lunch", limit=2)

    assert requested == [
        (
            "https://example.test/api/json/v1/1/filter.php?c=Quick%20Lunch",
            3,
        )
    ]
    assert [(item.external_id, item.name) for item in references] == [
        ("100", "First meal"),
        ("101", "Second meal"),
    ]


def test_themealdb_adapter_rejects_non_numeric_id_before_request() -> None:
    source = TheMealDbSource(
        api_key="1",
        base_url="https://example.test",
        timeout_seconds=3,
        fetch_json=lambda url, timeout: pytest.fail("request must not be sent"),
    )

    with pytest.raises(RecipeSourcePayloadError):
        source.fetch("not-an-id")


def test_themealdb_fetch_maps_network_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    def unavailable(request: object, timeout: float) -> object:
        raise URLError("offline")

    monkeypatch.setattr(recipe_sources, "urlopen", unavailable)

    with pytest.raises(RecipeSourceUnavailableError):
        recipe_sources.fetch_json("https://example.test", 3)


def test_themealdb_api_imports_idempotently_without_live_network() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base = RecipeImport.metadata
    Base.create_all(engine)
    with Session(engine) as seed_session, seed_session.begin():
        replace_catalog(seed_session, load_catalog())

    source = TheMealDbSource(
        api_key="1",
        base_url="https://example.test",
        timeout_seconds=3,
        fetch_json=lambda url, timeout: {"meals": [_source_payload()]},
    )

    def override_session() -> Iterator[Session]:
        with Session(engine) as api_session:
            yield api_session

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_themealdb_source] = lambda: source
    try:
        with TestClient(app) as client:
            first = client.post("/api/internal/recipe-imports/sources/themealdb/52771")
            second = client.post("/api/internal/recipe-imports/sources/themealdb/52771")

        assert first.status_code == 201
        assert first.json()["created"]
        assert first.json()["recipe_import"]["status"] == "needs_review"
        assert first.json()["recipe_import"]["raw_payload"]["idMeal"] == "52771"
        assert second.status_code == 200
        assert not second.json()["created"]
        assert (
            second.json()["recipe_import"]["id"] == first.json()["recipe_import"]["id"]
        )
        with Session(engine) as session:
            assert session.scalar(select(func.count()).select_from(RecipeImport)) == 1
    finally:
        app.dependency_overrides.clear()


def test_themealdb_api_imports_and_reprocesses_category_batch() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base = RecipeImport.metadata
    Base.create_all(engine)
    with Session(engine) as seed_session, seed_session.begin():
        replace_catalog(seed_session, load_catalog())

    def fetch_json(url: str, timeout: float) -> dict[str, object]:
        if "filter.php" in url:
            return {
                "meals": [
                    {"idMeal": "52771", "strMeal": "Spicy Arrabiata Penne"}
                ]
            }
        return {"meals": [_source_payload()]}

    source = TheMealDbSource(
        api_key="1",
        base_url="https://example.test",
        timeout_seconds=3,
        fetch_json=fetch_json,
    )

    def override_session() -> Iterator[Session]:
        with Session(engine) as api_session:
            yield api_session

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_themealdb_source] = lambda: source
    try:
        with TestClient(app) as client:
            first = client.post(
                "/api/internal/recipe-imports/sources/themealdb/"
                "batches/categories/Vegetarian",
                params={"limit": 1},
            )
            second = client.post(
                "/api/internal/recipe-imports/sources/themealdb/"
                "batches/categories/Vegetarian",
                params={"limit": 1},
            )
            queue = client.get("/api/internal/recipe-imports")
            reprocessed = client.post("/api/internal/recipe-imports/reprocess")

        assert first.status_code == 200
        assert first.json()["discovered"] == 1
        assert first.json()["created"] == 1
        assert first.json()["results"][0]["recipe_import"]["quality_score"] < 100
        assert second.status_code == 200
        assert second.json()["created"] == 0
        assert len(queue.json()) == 1
        assert queue.json()[0]["review_priority"] in {
            "medium_effort",
            "high_effort",
        }
        assert reprocessed.status_code == 200
        assert reprocessed.json()["reprocessed"] == 1
    finally:
        app.dependency_overrides.clear()


def _source_payload() -> dict[str, object]:
    value = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value
