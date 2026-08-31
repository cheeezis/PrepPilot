from collections.abc import Iterator
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from preppilot_api.catalog_data import load_catalog
from preppilot_api.catalog_repository import load_catalog_from_database
from preppilot_api.catalog_seed import replace_catalog
from preppilot_api.models import (
    Base,
    Meal,
    MealIngredient,
    MealOrigin,
    MealRole,
    RecipeImport,
    RecipeImportStatus,
)
from preppilot_api.recipe_catalog_promotion import (
    PromoteRecipeImportCommand,
    RecipePromotionError,
    promote_recipe_import,
)
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


def test_promotes_ready_import_idempotently(session: Session) -> None:
    recipe_import = _ready_import(session)
    command = _promotion_command()

    meal, created = promote_recipe_import(session, recipe_import.id, command)
    repeated_meal, repeated_created = promote_recipe_import(
        session, recipe_import.id, command
    )

    assert created
    assert not repeated_created
    assert repeated_meal.id == meal.id
    assert meal.origin == MealOrigin.RECIPE_IMPORT
    assert meal.source_recipe_import_id == recipe_import.id
    assert session.scalar(
        select(func.count()).select_from(MealIngredient).where(
            MealIngredient.meal_id == meal.id
        )
    ) == 2


def test_rejects_import_that_still_needs_review(session: Session) -> None:
    recipe_import, _ = create_recipe_import(
        session,
        CreateRecipeImportCommand(
            source_name="test",
            external_id="unknown",
            payload=ExternalRecipePayload(
                title="Unknown meal",
                servings="1",
                instructions="Test.",
                ingredients=(
                    ExternalIngredientPayload(
                        line="100 g unknown",
                        name="Unknown ingredient",
                        amount="100",
                        unit="g",
                    ),
                ),
            ),
        ),
    )
    assert recipe_import.status == RecipeImportStatus.NEEDS_REVIEW

    with pytest.raises(RecipePromotionError, match="not ready"):
        promote_recipe_import(session, recipe_import.id, _promotion_command())


def test_imported_meal_survives_catalog_reseed_and_is_loaded(
    session: Session,
) -> None:
    recipe_import = _ready_import(session)
    meal, _ = promote_recipe_import(session, recipe_import.id, _promotion_command())

    replace_catalog(session, load_catalog())
    session.flush()

    assert session.scalar(select(func.count()).select_from(Meal)) == 11
    preserved = session.scalar(select(Meal).where(Meal.id == meal.id))
    assert preserved is not None
    assert preserved.origin == MealOrigin.RECIPE_IMPORT
    database_catalog = load_catalog_from_database(session)
    promoted = next(
        catalog_meal
        for catalog_meal in database_catalog.meals
        if catalog_meal.key == "imported_chicken_shake"
    )
    assert promoted.roles == (MealRole.MAIN_MEAL,)
    assert promoted.portion_factors == (Decimal("1.0"), Decimal("1.5"))


def _ready_import(session: Session) -> RecipeImport:
    recipe_import, _ = create_recipe_import(
        session,
        CreateRecipeImportCommand(
            source_name="test",
            external_id="ready",
            payload=ExternalRecipePayload(
                title="Chicken shake",
                servings="2",
                instructions="Prepare and divide.",
                ingredients=(
                    ExternalIngredientPayload(
                        line="400 g chicken",
                        name="Chicken breast, raw",
                        amount="400",
                        unit="g",
                    ),
                    ExternalIngredientPayload(
                        line="1 l milk",
                        name="Milk, 1.5% fat",
                        amount="1",
                        unit="l",
                    ),
                ),
            ),
        ),
    )
    assert recipe_import.status == RecipeImportStatus.READY_FOR_CATALOG_REVIEW
    return recipe_import


def _promotion_command() -> PromoteRecipeImportCommand:
    return PromoteRecipeImportCommand(
        catalog_key="imported_chicken_shake",
        name="Imported chicken shake",
        preparation_minutes=10,
        instructions="Prepare and divide.",
        roles=(MealRole.MAIN_MEAL,),
        portion_factors=(Decimal("1.0"), Decimal("1.5")),
    )
