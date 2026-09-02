from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from preppilot_api.models import Recipe
from preppilot_api.nutrition import Nutrients


class RecipeCatalogUnavailableError(RuntimeError):
    pass


@dataclass(frozen=True)
class RecipeDefinition:
    id: int
    title: str
    servings: int
    source_url: str
    license_name: str
    attribution_text: str
    ingredients: tuple[str, ...]
    instructions: tuple[str, ...]
    nutrients: Nutrients


def load_recipes(session: Session) -> tuple[RecipeDefinition, ...]:
    rows = session.scalars(select(Recipe).order_by(Recipe.id)).all()
    if not rows:
        raise RecipeCatalogUnavailableError("no recipes available")
    return tuple(
        RecipeDefinition(
            id=row.id,
            title=row.title,
            servings=row.servings,
            source_url=row.source_url,
            license_name=row.license_name,
            attribution_text=row.attribution_text,
            ingredients=tuple(row.ingredients),
            instructions=tuple(row.instructions),
            nutrients=Nutrients(
                calories=Decimal(row.calories_per_serving),
                protein=Decimal(row.protein_per_serving),
                carbs=Decimal(row.carbs_per_serving),
                fat=Decimal(row.fat_per_serving),
            ),
        )
        for row in rows
    )
