import json
from decimal import Decimal
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from preppilot_api.catalog_data import load_catalog
from preppilot_api.catalog_repository import load_catalog_from_database
from preppilot_api.catalog_seed import replace_catalog
from preppilot_api.models import Base, MealRole, RecipeImportStatus
from preppilot_api.recipe_catalog_promotion import (
    PromoteRecipeImportCommand,
    promote_recipe_import,
)
from preppilot_api.recipe_imports import (
    CreateRecipeImportCommand,
    create_recipe_import,
)

FIXTURE = Path(__file__).parent / "fixtures/recipe_imports/metric_chicken_rice.json"


def test_source_independent_recipe_reaches_productive_catalog() -> None:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    command = CreateRecipeImportCommand.model_validate(fixture)
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    with Session(engine) as session, session.begin():
        replace_catalog(session, load_catalog())
        recipe_import, _ = create_recipe_import(session, command)
        assert recipe_import.status == RecipeImportStatus.READY_FOR_CATALOG_REVIEW

        meal, created = promote_recipe_import(
            session,
            recipe_import.id,
            PromoteRecipeImportCommand(
                catalog_key="imported_chicken_rice",
                name="Chicken with rice and broccoli",
                preparation_minutes=25,
                instructions=command.payload.instructions,
                roles=(MealRole.MAIN_MEAL,),
                portion_factors=(Decimal("0.5"), Decimal(1), Decimal("1.5")),
            ),
        )
        assert created
        assert meal.source_recipe_import_id == recipe_import.id

    with Session(engine) as session:
        catalog = load_catalog_from_database(session)
        assert "imported_chicken_rice" in {meal.key for meal in catalog.meals}
