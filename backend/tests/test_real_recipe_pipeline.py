import json
from decimal import Decimal
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from preppilot_api.catalog_data import load_catalog
from preppilot_api.catalog_repository import load_catalog_from_database
from preppilot_api.catalog_seed import replace_catalog
from preppilot_api.models import (
    Base,
    MealRole,
    RecipeImportStatus,
    ReviewDecisionAction,
)
from preppilot_api.recipe_catalog_promotion import (
    PromoteRecipeImportCommand,
    promote_recipe_import,
)
from preppilot_api.recipe_imports import (
    ReviewDecisionCommand,
    apply_review_decision,
    create_recipe_import,
    ingredients_for_import,
)
from preppilot_api.recipe_sources import TheMealDbSource

FIXTURE = (
    Path(__file__).parent / "fixtures/recipe_imports/themealdb_banana_pancakes.json"
)


def test_real_banana_pancakes_reach_productive_catalog() -> None:
    source_payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert isinstance(source_payload, dict)
    source = TheMealDbSource(
        api_key="1",
        base_url="https://example.test",
        timeout_seconds=3,
        fetch_json=lambda url, timeout: {"meals": [source_payload]},
    )
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    with Session(engine) as session, session.begin():
        replace_catalog(session, load_catalog())
        fetched = source.fetch("52855")
        recipe_import, _ = create_recipe_import(
            session,
            fetched.command,
            source_payload=fetched.source_payload,
        )
        assert recipe_import.status == RecipeImportStatus.NEEDS_REVIEW

        apply_review_decision(
            session,
            recipe_import.id,
            ReviewDecisionCommand(
                action=ReviewDecisionAction.SET_SERVINGS,
                amount=Decimal(2),
            ),
        )
        ingredients = {
            ingredient.raw_name: ingredient
            for ingredient in ingredients_for_import(session, recipe_import.id)
        }
        for name in ("Baking Powder", "Vanilla Extract"):
            apply_review_decision(
                session,
                recipe_import.id,
                ReviewDecisionCommand(
                    action=ReviewDecisionAction.EXCLUDE,
                    ingredient_id=ingredients[name].id,
                ),
            )

        assert recipe_import.status == RecipeImportStatus.READY_FOR_CATALOG_REVIEW
        normalized = {
            ingredient.raw_name: ingredient.normalized_amount
            for ingredient in ingredients_for_import(session, recipe_import.id)
            if not ingredient.excluded
        }
        assert normalized == {
            "Banana": Decimal("68.000"),
            "Eggs": Decimal("44.000"),
            "Oil": Decimal("2.500"),
            "Pecan Nuts": Decimal("12.500"),
            "Raspberries": Decimal("62.500"),
        }

        meal, created = promote_recipe_import(
            session,
            recipe_import.id,
            PromoteRecipeImportCommand(
                catalog_key="themealdb_banana_pancakes",
                name="Banana pancakes with pecans and raspberries",
                preparation_minutes=10,
                instructions=fetched.command.payload.instructions,
                roles=(MealRole.FIRST_MEAL,),
                portion_factors=(Decimal("0.5"), Decimal(1), Decimal("1.5")),
            ),
        )
        assert created
        assert meal.source_recipe_import_id == recipe_import.id

    with Session(engine) as session:
        catalog = load_catalog_from_database(session)
        assert "themealdb_banana_pancakes" in {meal.key for meal in catalog.meals}
