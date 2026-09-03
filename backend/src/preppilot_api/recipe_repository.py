from dataclasses import dataclass
from decimal import Decimal
from typing import Literal, cast

from sqlalchemy import select
from sqlalchemy.orm import Session

from preppilot_api.models import Recipe
from preppilot_api.nutrition import Nutrients


class RecipeCatalogUnavailableError(RuntimeError):
    pass


RecipeCategory = Literal["breakfast", "lunch", "dinner", "snack"]


@dataclass(frozen=True)
class RecipeDefinition:
    id: int
    title: str
    categories: tuple[RecipeCategory, ...]
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
            categories=tuple(cast(RecipeCategory, value) for value in row.categories),
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
                sugar=_optional_decimal(row.sugar_per_serving),
                saturated_fat=_optional_decimal(row.saturated_fat_per_serving),
                fiber=_optional_decimal(row.fiber_per_serving),
                salt=_optional_decimal(row.salt_per_serving),
            ),
        )
        for row in rows
    )


def _optional_decimal(value: Decimal | None) -> Decimal | None:
    return None if value is None else Decimal(value)
