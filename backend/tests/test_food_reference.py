import csv
import io
import zipfile
from collections.abc import Iterator
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from preppilot_api.database import get_session
from preppilot_api.food_auto_resolution import canonical_catalog_key
from preppilot_api.food_reference import (
    FoodReferenceDataset,
    FoodReferenceSource,
    get_food_reference_source,
    import_food_references,
    parse_food_reference_archive,
)
from preppilot_api.food_sources import (
    FoodDataCentralSource,
    get_fooddata_central_source,
)
from preppilot_api.main import app
from preppilot_api.models import (
    Base,
    Food,
    FoodAlias,
    FoodReferenceItem,
    RecipeImport,
    RecipeImportStatus,
)


def test_parses_and_imports_fdc_csv_archive_idempotently() -> None:
    records = parse_food_reference_archive(
        _archive(), FoodReferenceDataset.FOUNDATION
    )

    assert len(records) == 2
    assert records[0].external_id == "1001"
    assert records[0].food_category == "Vegetables"
    assert records[0].calories_per_100 == 41
    assert records[0].carbs_per_100 == Decimal("8.2")
    assert records[0].portions == (
        {"gram_weight": "61", "amount": "1", "description": "medium"},
    )

    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as session, session.begin():
        first = import_food_references(
            session, FoodReferenceDataset.FOUNDATION, records
        )
        second = import_food_references(
            session, FoodReferenceDataset.FOUNDATION, records
        )

    assert (first.created, first.updated, first.unchanged, first.complete) == (
        2,
        0,
        0,
        1,
    )
    assert (second.created, second.updated, second.unchanged) == (0, 0, 2)
    with Session(engine) as session:
        assert (
            session.scalar(select(func.count()).select_from(FoodReferenceItem)) == 2
        )


def test_canonical_catalog_key_singularizes_common_recipe_plurals() -> None:
    assert canonical_catalog_key("Carrots", "1") == "carrot"
    assert canonical_catalog_key("Sun-Dried Tomatoes", "2") == "sun_dried_tomato"


def test_internal_api_bulk_imports_and_searches_local_reference() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    def override_session() -> Iterator[Session]:
        with Session(engine) as session:
            yield session

    source = FoodReferenceSource(fetch_bytes=lambda url, timeout: _archive())
    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_food_reference_source] = lambda: source
    app.dependency_overrides[get_fooddata_central_source] = lambda: (
        FoodDataCentralSource(
            api_key="unused",
            base_url="https://example.test",
            timeout_seconds=1,
            fetch_json=lambda url, timeout: _unexpected_fdc_request(),
        )
    )
    try:
        with TestClient(app) as client:
            first = client.post(
                "/api/internal/food-references/sources/fooddata-central/foundation"
            )
            second = client.post(
                "/api/internal/food-references/sources/fooddata-central/foundation"
            )
            stats = client.get("/api/internal/food-references/stats")
            search = client.get(
                "/api/internal/food-references/search",
                params={"query": "Carrots", "limit": 2},
            )
            recipe = client.post(
                "/api/internal/recipe-imports",
                json={
                    "source_name": "test",
                    "external_id": "carrot-reference-recipe",
                    "payload": {
                        "title": "Carrot dish",
                        "servings": "2",
                        "instructions": (
                            "Prepare the carrots carefully, cook them thoroughly, "
                            "and serve the finished dish while it is still warm."
                        ),
                        "ingredients": [
                            {
                                "line": "200 g Carrots",
                                "name": "Carrots",
                                "amount": "200",
                                "unit": "g",
                            }
                        ],
                    },
                },
            )
            suggested = client.post(
                "/api/internal/food-imports/suggestions/from-recipe-inbox",
                params={"limit": 5},
            )
            repeated_suggestion = client.post(
                "/api/internal/food-imports/suggestions/from-recipe-inbox",
                params={"limit": 5},
            )
            dry_run = client.post(
                "/api/internal/food-imports/auto-resolve/from-recipe-inbox",
                params={"limit": 5, "dry_run": True},
            )
            resolved = client.post(
                "/api/internal/food-imports/auto-resolve/from-recipe-inbox",
                params={"limit": 5, "dry_run": False},
            )
            repeated_resolution = client.post(
                "/api/internal/food-imports/auto-resolve/from-recipe-inbox",
                params={"limit": 5, "dry_run": False},
            )
    finally:
        app.dependency_overrides.clear()

    assert first.status_code == 200
    assert first.json() == {
        "dataset": "foundation",
        "parsed": 2,
        "created": 2,
        "updated": 0,
        "unchanged": 0,
        "complete": 1,
    }
    assert second.json()["unchanged"] == 2
    assert stats.json() == {
        "total": 2,
        "complete": 1,
        "by_data_type": {"Foundation": 2},
    }
    assert search.status_code == 200
    assert search.json()[0]["fdc_id"] == "1001"
    assert search.json()[0]["description"] == "Carrots, raw"
    assert recipe.status_code == 201
    assert suggested.json()["selected"] == 1
    assert suggested.json()["created"] == 1
    assert suggested.json()["suggestions"][0]["selected_fdc_id"] == "1001"
    assert repeated_suggestion.json()["created"] == 0
    assert dry_run.json()["eligible"] == 1
    assert dry_run.json()["promoted"] == 0
    assert resolved.json()["promoted"] == 1
    assert resolved.json()["aliases_added"] == 1
    assert resolved.json()["ready_recipes_before"] == 0
    assert resolved.json()["ready_recipes_after"] == 1
    assert repeated_resolution.json()["processed"] == 0
    with Session(engine) as session:
        assert session.scalar(select(func.count()).select_from(Food)) == 1
        assert session.scalar(select(func.count()).select_from(FoodAlias)) == 1
        recipe_import = session.scalar(select(RecipeImport))
        assert recipe_import is not None
        assert recipe_import.status == RecipeImportStatus.READY_FOR_CATALOG_REVIEW


def _unexpected_fdc_request() -> dict[str, object]:
    raise AssertionError("local food references must avoid individual FDC requests")


def _archive() -> bytes:
    files = {
        "foundation_food.csv": [{"fdc_id": "1001"}, {"fdc_id": "1002"}],
        "food.csv": [
            {
                "fdc_id": "1001",
                "data_type": "Foundation",
                "description": "Carrots, raw",
                "food_category_id": "11",
                "publication_date": "2026-04-30",
            },
            {
                "fdc_id": "1002",
                "data_type": "Foundation",
                "description": "Mystery vegetable",
                "food_category_id": "11",
                "publication_date": "2026-04-30",
            },
        ],
        "food_category.csv": [{"id": "11", "description": "Vegetables"}],
        "measure_unit.csv": [{"id": "9999", "name": "each"}],
        "food_nutrient.csv": [
            {"fdc_id": "1001", "nutrient_id": "1008", "amount": "41"},
            {"fdc_id": "1001", "nutrient_id": "1003", "amount": "0.93"},
            {"fdc_id": "1001", "nutrient_id": "1004", "amount": "0.24"},
            {"fdc_id": "1001", "nutrient_id": "1005", "amount": "9.6"},
            {"fdc_id": "1001", "nutrient_id": "1079", "amount": "1.4"},
        ],
        "food_portion.csv": [
            {
                "fdc_id": "1001",
                "amount": "1",
                "measure_unit_id": "9999",
                "portion_description": "medium",
                "modifier": "",
                "gram_weight": "61",
            }
        ],
    }
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        for filename, rows in files.items():
            text = io.StringIO()
            writer = csv.DictWriter(text, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
            archive.writestr(filename, text.getvalue())
    return output.getvalue()
