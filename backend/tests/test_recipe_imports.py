import json
from collections.abc import Iterator
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from preppilot_api.catalog_data import load_catalog
from preppilot_api.catalog_seed import replace_catalog
from preppilot_api.models import (
    Base,
    FoodAlias,
    FoodMeasureDefault,
    FoodSourceIdentifier,
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
    resolve_recipe_ingredient_identity,
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
    assert (
        session.scalar(
            select(func.count())
            .select_from(FoodAlias)
            .where(FoodAlias.source_name == "fixture-recipes")
        )
        == 1
    )

    assert session.scalar(select(func.count()).select_from(ImportReviewDecision)) == 1

    replace_catalog(session, load_catalog())
    session.flush()

    assert recipe_import.status == RecipeImportStatus.READY_FOR_CATALOG_REVIEW
    assert (
        session.scalar(
            select(func.count())
            .select_from(FoodAlias)
            .where(FoodAlias.source_name == "fixture-recipes")
        )
        == 1
    )


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
    assert (
        session.scalar(
            select(func.count())
            .select_from(FoodMeasureDefault)
            .where(FoodMeasureDefault.source_name == "FoodData Central test reference")
        )
        == 1
    )

    replace_catalog(session, load_catalog())
    session.flush()

    assert (
        session.scalar(
            select(func.count())
            .select_from(FoodMeasureDefault)
            .where(FoodMeasureDefault.source_name == "FoodData Central test reference")
        )
        == 1
    )


def test_one_source_identity_resolution_reprocesses_multiple_recipes(
    session: Session,
) -> None:
    identity = {
        "source_name": "wikibooks",
        "external_id": "12345",
        "source_label": "Cookbook:Tomato",
        "source_url": "https://en.wikibooks.org/wiki/Cookbook:Tomato",
    }
    first = CreateRecipeImportCommand.model_validate(
        _identity_recipe("wikibooks-recipe-1", identity)
    )
    second = CreateRecipeImportCommand.model_validate(
        _identity_recipe("wikibooks-recipe-2", identity)
    )

    first_import, _ = create_recipe_import(session, first)
    second_import, _ = create_recipe_import(session, second)
    first_ingredient = ingredients_for_import(session, first_import.id)[0]
    second_ingredient = ingredients_for_import(session, second_import.id)[0]

    assert first_import.status == RecipeImportStatus.NEEDS_REVIEW
    assert second_import.status == RecipeImportStatus.NEEDS_REVIEW
    assert first_ingredient.source_identifier_id == second_ingredient.source_identifier_id
    assert session.scalar(select(func.count()).select_from(FoodSourceIdentifier)) == 1

    identifier_id = first_ingredient.source_identifier_id
    assert identifier_id is not None
    _, changed = resolve_recipe_ingredient_identity(
        session,
        identifier_id=identifier_id,
        concept_key="tomato",
    )
    reprocessed_first = session.get(RecipeImport, first_import.id)
    reprocessed_second = session.get(RecipeImport, second_import.id)

    assert changed
    assert reprocessed_first is not None
    assert reprocessed_second is not None
    assert reprocessed_first.status == RecipeImportStatus.READY_FOR_CATALOG_REVIEW
    assert reprocessed_second.status == RecipeImportStatus.READY_FOR_CATALOG_REVIEW
    assert first_ingredient.concept_id == second_ingredient.concept_id
    assert first_ingredient.food_id == second_ingredient.food_id


def _identity_recipe(
    external_id: str, identity: dict[str, str]
) -> dict[str, object]:
    return {
        "source_name": "wikibooks",
        "external_id": external_id,
        "payload": {
            "title": external_id,
            "servings": "2",
            "instructions": "Prepare the recipe.",
            "ingredients": [
                {
                    "line": "200 g tomato",
                    "name": "unknown source label",
                    "amount": "200",
                    "unit": "g",
                    "identity": identity,
                }
            ],
        },
    }


def _command(name: str) -> CreateRecipeImportCommand:
    return CreateRecipeImportCommand.model_validate(_fixture_value(name))


def _fixture_value(name: str) -> dict[str, object]:
    value = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value
