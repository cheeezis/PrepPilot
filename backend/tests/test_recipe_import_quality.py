from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from preppilot_api.catalog_data import load_catalog
from preppilot_api.catalog_seed import replace_catalog
from preppilot_api.models import Base, RecipeImportStatus
from preppilot_api.recipe_import_quality import ReviewPriority, assess_recipe_import
from preppilot_api.recipe_imports import (
    CreateRecipeImportCommand,
    ExternalIngredientPayload,
    ExternalRecipePayload,
    create_recipe_import,
)


@pytest.fixture
def session() -> Iterator[Session]:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as database_session, database_session.begin():
        replace_catalog(database_session, load_catalog())
    with Session(engine) as database_session:
        yield database_session


def test_assessment_routes_thin_source_data_to_low_quality(
    session: Session,
) -> None:
    recipe_import, _ = create_recipe_import(
        session,
        CreateRecipeImportCommand(
            source_name="test",
            external_id="thin-recipe",
            payload=ExternalRecipePayload(
                title="Bread omelette",
                servings=None,
                instructions="Make and enjoy",
                ingredients=(
                    ExternalIngredientPayload(
                        line="2 Bread", name="Bread", amount="2"
                    ),
                    ExternalIngredientPayload(line="2 Egg", name="Egg", amount="2"),
                ),
            ),
        ),
    )

    assessment = assess_recipe_import(session, recipe_import)

    assert assessment.priority == ReviewPriority.LOW_QUALITY
    assert assessment.score == 34
    assert assessment.issues == (
        "missing_serving_count",
        "insufficient_instructions",
        "unknown_foods",
    )
    assert assessment.unknown_ingredient_count == 1
    assert assessment.review_item_count == 2


def test_assessment_prioritizes_small_review_candidates(session: Session) -> None:
    recipe_import, _ = create_recipe_import(
        session,
        CreateRecipeImportCommand(
            source_name="test",
            external_id="small-review",
            payload=ExternalRecipePayload(
                title="Simple chicken",
                servings="2",
                instructions=(
                    "Season the chicken thoroughly, cook it in a hot pan until done, "
                    "then rest it briefly before slicing and serving."
                ),
                ingredients=(
                    ExternalIngredientPayload(
                        line="400 g chicken breasts",
                        name="chicken breasts",
                        amount="400",
                        unit="g",
                    ),
                    ExternalIngredientPayload(
                        line="1 tsp mystery spice",
                        name="mystery spice",
                        amount="1",
                        unit="tsp",
                    ),
                ),
            ),
        ),
    )

    assessment = assess_recipe_import(session, recipe_import)

    assert assessment.priority == ReviewPriority.LOW_EFFORT
    assert assessment.score == 94
    assert assessment.issues == ("unknown_foods",)
    assert assessment.review_item_count == 1


def test_assessment_places_rejected_imports_last(session: Session) -> None:
    recipe_import, _ = create_recipe_import(
        session,
        CreateRecipeImportCommand(
            source_name="test",
            external_id="rejected",
            payload=ExternalRecipePayload(
                title="Rejected recipe",
                servings="2",
                instructions=(
                    "Cook the eggs carefully in a hot pan, turn them once, and serve "
                    "them immediately while they are still warm."
                ),
                ingredients=(
                    ExternalIngredientPayload(
                        line="2 eggs", name="Eggs", amount="2", unit="eggs"
                    ),
                ),
            ),
        ),
    )
    recipe_import.status = RecipeImportStatus.REJECTED
    session.flush()

    assessment = assess_recipe_import(session, recipe_import)

    assert assessment.priority == ReviewPriority.REJECTED
