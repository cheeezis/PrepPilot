import argparse

import httpx2
from sqlalchemy.orm import Session

from preppilot_api.catalog_data import load_catalog_configuration
from preppilot_api.config import get_settings
from preppilot_api.database import engine
from preppilot_api.food_data_central import FoodDataCentralClient
from preppilot_api.food_resolution import FoodResolutionError, FoodResolver
from preppilot_api.models import MealRole
from preppilot_api.recipe_import import RecipeImportOptions, import_themealdb_recipe
from preppilot_api.themealdb import TheMealDbClient


def main() -> None:
    args = _parse_args()
    settings = get_settings()
    if settings.food_data_central_api_key is None:
        raise SystemExit(
            "PREPPILOT_FOOD_DATA_CENTRAL_API_KEY must be set before importing"
        )

    options = RecipeImportOptions(
        source_servings=args.source_servings,
        preparation_minutes=args.preparation_minutes,
        role=MealRole(args.role),
    )
    catalog = load_catalog_configuration()
    try:
        with (
            TheMealDbClient(settings.themealdb_api_key) as recipe_source,
            FoodDataCentralClient(settings.food_data_central_api_key) as food_source,
            Session(engine) as session,
        ):
            meal = import_themealdb_recipe(
                session=session,
                meal_id=args.meal_id,
                options=options,
                recipe_source=recipe_source,
                ingredient_resolver=FoodResolver(
                    food_source,
                    preferred_fdc_ids=catalog.preferred_fdc_ids,
                    catalog_foods=catalog.foods,
                    catalog_portions=catalog.portions,
                ),
            )
            print(f"Imported meal {meal.id}: {meal.name}")
    except FoodResolutionError as error:
        raise SystemExit(f"Import stopped: {error}") from None
    except httpx2.HTTPError as error:
        raise SystemExit(f"External API request failed: {error}") from None


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import a TheMealDB catalog meal")
    parser.add_argument("meal_id")
    parser.add_argument("--source-servings", type=int, required=True)
    parser.add_argument("--preparation-minutes", type=int, required=True)
    parser.add_argument(
        "--role",
        choices=[role.value for role in MealRole],
        required=True,
    )
    return parser.parse_args()


if __name__ == "__main__":
    main()
