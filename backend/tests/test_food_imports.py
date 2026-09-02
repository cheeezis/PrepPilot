from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from preppilot_api.catalog_data import load_catalog
from preppilot_api.catalog_repository import load_catalog_from_database
from preppilot_api.catalog_seed import replace_catalog
from preppilot_api.food_imports import (
    CreateFoodImportCommand,
    FoodImportPromotionError,
    PromoteFoodImportCommand,
    create_food_import,
    find_latest_food_import,
    promote_food_import,
)
from preppilot_api.models import Base, FoodImport, FoodImportStatus, FoodOrigin


def test_food_import_promotes_idempotently_and_survives_seed() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    with Session(engine) as session, session.begin():
        replace_catalog(session, load_catalog())
        first, created = create_food_import(session, _command())
        repeated, repeated_created = create_food_import(session, _command())

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
        assert "garlic" in {food.key for food in catalog.foods}
        assert session.scalar(select(func.count()).select_from(FoodImport)) == 1


def test_incomplete_food_import_stays_behind_review_boundary() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    incomplete = _command(
        carbs_per_100=None,
        review_reasons=("missing_fiber",),
    )

    with Session(engine) as session, session.begin():
        food_import, _ = create_food_import(session, incomplete)
        assert food_import.status == FoodImportStatus.NEEDS_REVIEW
        with pytest.raises(FoodImportPromotionError):
            promote_food_import(
                session,
                food_import.id,
                PromoteFoodImportCommand(catalog_key="garlic", name="Garlic"),
            )


def test_finds_latest_food_import_by_stable_source_identity() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    with Session(engine) as session, session.begin():
        first, _ = create_food_import(session, _command())
        second, _ = create_food_import(
            session,
            _command(raw_payload={"description": "Garlic", "revision": 2}),
        )
        found = find_latest_food_import(session, "nutrition-reference", "garlic")
        first_id = first.id
        second_id = second.id
        found_id = found.id if found is not None else None

    assert first_id != second_id
    assert found_id == second_id


def _command(
    *,
    raw_payload: dict[str, object] | None = None,
    carbs_per_100: Decimal | None = Decimal("30.96"),
    review_reasons: tuple[str, ...] = (),
) -> CreateFoodImportCommand:
    return CreateFoodImportCommand(
        source_name="nutrition-reference",
        external_id="garlic",
        fetched_at=datetime(2026, 9, 1, tzinfo=UTC),
        raw_payload=raw_payload or {"description": "Garlic", "revision": 1},
        candidate_name="Garlic, raw",
        calories_per_100=Decimal(149),
        protein_per_100=Decimal("6.36"),
        carbs_per_100=carbs_per_100,
        fat_per_100=Decimal("0.5"),
        review_reasons=review_reasons,
    )
