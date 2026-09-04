from dataclasses import dataclass
from decimal import Decimal
from typing import Literal, cast

from sqlalchemy import select
from sqlalchemy.orm import Session

from preppilot_api.models import Recipe
from preppilot_api.nutrition import Nutrients

RecipeCategory = Literal["breakfast", "lunch", "dinner", "snack"]


@dataclass(frozen=True)
class RecipeIngredient:
    amount: Decimal
    unit: str
    name: str


@dataclass(frozen=True)
class RecipeDefinition:
    id: int
    title: str
    categories: tuple[RecipeCategory, ...]
    servings: int
    source_url: str | None
    ingredients: tuple[RecipeIngredient, ...]
    instructions: tuple[str, ...]
    preparation_minutes: int | None
    cooking_minutes: int | None
    nutrients: Nutrients


@dataclass(frozen=True)
class RecipeValues:
    title: str
    categories: tuple[RecipeCategory, ...]
    servings: int
    source_url: str | None
    ingredients: tuple[RecipeIngredient, ...]
    instructions: tuple[str, ...]
    preparation_minutes: int | None
    cooking_minutes: int | None
    nutrients: Nutrients


def load_recipes(session: Session) -> tuple[RecipeDefinition, ...]:
    rows = session.scalars(select(Recipe).order_by(Recipe.id)).all()
    return tuple(_to_definition(row) for row in rows)


def create_recipe(session: Session, values: RecipeValues) -> RecipeDefinition:
    row = Recipe()
    _apply_values(row, values)
    session.add(row)
    session.commit()
    session.refresh(row)
    return _to_definition(row)


def update_recipe(
    session: Session, recipe_id: int, values: RecipeValues
) -> RecipeDefinition | None:
    row = session.get(Recipe, recipe_id)
    if row is None:
        return None
    _apply_values(row, values)
    session.commit()
    session.refresh(row)
    return _to_definition(row)


def delete_recipe(session: Session, recipe_id: int) -> bool:
    row = session.get(Recipe, recipe_id)
    if row is None:
        return False
    session.delete(row)
    session.commit()
    return True


def _apply_values(row: Recipe, values: RecipeValues) -> None:
    row.title = values.title
    row.categories = list(values.categories)
    row.servings = values.servings
    row.source_url = values.source_url
    row.ingredients = [
        {
            "amount": str(ingredient.amount),
            "unit": ingredient.unit,
            "name": ingredient.name,
        }
        for ingredient in values.ingredients
    ]
    row.instructions = list(values.instructions)
    row.preparation_minutes = values.preparation_minutes
    row.cooking_minutes = values.cooking_minutes
    row.calories_per_serving = values.nutrients.calories
    row.protein_per_serving = values.nutrients.protein
    row.carbs_per_serving = values.nutrients.carbs
    row.fat_per_serving = values.nutrients.fat
    row.sugar_per_serving = values.nutrients.sugar
    row.saturated_fat_per_serving = values.nutrients.saturated_fat
    row.fiber_per_serving = values.nutrients.fiber
    row.salt_per_serving = values.nutrients.salt


def _to_definition(row: Recipe) -> RecipeDefinition:
    return RecipeDefinition(
        id=row.id,
        title=row.title,
        categories=tuple(cast(RecipeCategory, value) for value in row.categories),
        servings=row.servings,
        source_url=row.source_url,
        ingredients=tuple(
            RecipeIngredient(
                amount=Decimal(str(ingredient["amount"])),
                unit=str(ingredient["unit"]),
                name=str(ingredient["name"]),
            )
            for ingredient in row.ingredients
        ),
        instructions=tuple(row.instructions),
        preparation_minutes=row.preparation_minutes,
        cooking_minutes=row.cooking_minutes,
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


def _optional_decimal(value: Decimal | None) -> Decimal | None:
    return None if value is None else Decimal(value)
