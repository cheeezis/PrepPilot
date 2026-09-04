from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal, cast

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from preppilot_api.database import get_session
from preppilot_api.models import (
    Food,
    FoodPortion,
    Recipe,
    RecipeIngredient,
    RecipeMealRole,
)
from preppilot_api.nutrition import Nutrients, calculate_recipe_nutrition

MealRole = Literal["breakfast", "lunch", "dinner", "snack"]
MEAL_ROLE_ORDER: tuple[MealRole, ...] = (
    "breakfast",
    "lunch",
    "dinner",
    "snack",
)

router = APIRouter(prefix="/api/recipes", tags=["recipes"])
DatabaseSession = Annotated[Session, Depends(get_session)]


class RecipeIngredientRequest(BaseModel):
    food_id: int = Field(gt=0)
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=3)
    food_portion_id: int | None = Field(default=None, gt=0)


class RecipeWriteRequest(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    servings: int = Field(gt=0)
    meal_roles: list[MealRole] = Field(min_length=1, max_length=4)
    ingredients: list[RecipeIngredientRequest] = Field(min_length=1)
    instructions: list[str] = Field(min_length=1)

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str) -> str:
        normalized = " ".join(value.split())
        if not normalized:
            raise ValueError("title must not be blank")
        return normalized

    @field_validator("meal_roles")
    @classmethod
    def meal_roles_must_be_unique(cls, value: list[MealRole]) -> list[MealRole]:
        if len(set(value)) != len(value):
            raise ValueError("meal roles must be unique")
        return value

    @field_validator("ingredients")
    @classmethod
    def foods_must_be_unique(
        cls, value: list[RecipeIngredientRequest]
    ) -> list[RecipeIngredientRequest]:
        if len({item.food_id for item in value}) != len(value):
            raise ValueError("foods must be unique within a recipe")
        return value

    @field_validator("instructions")
    @classmethod
    def normalize_instructions(cls, value: list[str]) -> list[str]:
        normalized = [" ".join(item.split()) for item in value]
        if any(not item for item in normalized):
            raise ValueError("instructions must not be blank")
        return normalized


class NutrientResponse(BaseModel):
    calories_kcal: float
    protein_g: float
    carbohydrates_g: float
    fat_g: float


class RecipeIngredientResponse(BaseModel):
    food_id: int
    food_name: str
    food_portion_id: int | None
    amount: float
    unit: str
    base_amount: float
    base_unit: Literal["g", "ml"]
    position: int


class RecipeResponse(BaseModel):
    id: int
    title: str
    servings: int
    is_meal_prep: bool
    meal_roles: list[MealRole]
    ingredients: list[RecipeIngredientResponse]
    instructions: list[str]
    nutrition_total: NutrientResponse
    nutrition_per_serving: NutrientResponse
    created_at: datetime
    updated_at: datetime


@router.get("", response_model=list[RecipeResponse])
def list_recipes(session: DatabaseSession) -> list[RecipeResponse]:
    try:
        recipes = session.scalars(
            select(Recipe).order_by(func.lower(Recipe.title), Recipe.id)
        ).all()
    except SQLAlchemyError as error:
        raise _database_unavailable() from error
    return [_serialize(recipe) for recipe in recipes]


@router.post("", response_model=RecipeResponse, status_code=status.HTTP_201_CREATED)
def create_recipe(
    request: RecipeWriteRequest, session: DatabaseSession
) -> RecipeResponse:
    recipe = Recipe()
    _apply_request(recipe, request, session)
    session.add(recipe)
    _commit(session)
    session.refresh(recipe)
    return _serialize(recipe)


@router.put("/{recipe_id}", response_model=RecipeResponse)
def update_recipe(
    recipe_id: int, request: RecipeWriteRequest, session: DatabaseSession
) -> RecipeResponse:
    recipe = _get_recipe(recipe_id, session)
    recipe.meal_roles.clear()
    recipe.ingredients.clear()
    try:
        session.flush()
    except SQLAlchemyError as error:
        session.rollback()
        raise _database_unavailable() from error
    _apply_request(recipe, request, session)
    _commit(session)
    session.refresh(recipe)
    return _serialize(recipe)


@router.delete("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recipe(recipe_id: int, session: DatabaseSession) -> Response:
    recipe = _get_recipe(recipe_id, session)
    session.delete(recipe)
    _commit(session)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _get_recipe(recipe_id: int, session: Session) -> Recipe:
    try:
        recipe = session.get(Recipe, recipe_id)
    except SQLAlchemyError as error:
        raise _database_unavailable() from error
    if recipe is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rezept nicht gefunden",
        )
    return recipe


def _apply_request(
    recipe: Recipe, request: RecipeWriteRequest, session: Session
) -> None:
    foods = _load_foods(request.ingredients, session)
    portions = _load_portions(request.ingredients, session)
    recipe.title = request.title
    recipe.servings = request.servings
    recipe.instructions = request.instructions
    recipe.meal_roles = [
        RecipeMealRole(meal_role=role)
        for role in MEAL_ROLE_ORDER
        if role in request.meal_roles
    ]
    recipe.ingredients = [
        RecipeIngredient(
            food_id=item.food_id,
            food_portion_id=item.food_portion_id,
            amount=item.amount,
            unit=foods[item.food_id].base_unit,
            position=position,
            food=foods[item.food_id],
            food_portion=(
                portions[item.food_portion_id]
                if item.food_portion_id is not None
                else None
            ),
        )
        for position, item in enumerate(request.ingredients)
    ]


def _load_foods(
    ingredients: list[RecipeIngredientRequest], session: Session
) -> dict[int, Food]:
    food_ids = [item.food_id for item in ingredients]
    try:
        foods = session.scalars(select(Food).where(Food.id.in_(food_ids))).all()
    except SQLAlchemyError as error:
        raise _database_unavailable() from error
    by_id = {food.id: food for food in foods}
    missing = [food_id for food_id in food_ids if food_id not in by_id]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Unbekannte Lebensmittel-ID: {missing[0]}",
        )
    return by_id


def _load_portions(
    ingredients: list[RecipeIngredientRequest], session: Session
) -> dict[int, FoodPortion]:
    portion_ids = [
        item.food_portion_id
        for item in ingredients
        if item.food_portion_id is not None
    ]
    if not portion_ids:
        return {}
    try:
        portions = session.scalars(
            select(FoodPortion).where(FoodPortion.id.in_(portion_ids))
        ).all()
    except SQLAlchemyError as error:
        raise _database_unavailable() from error
    by_id = {portion.id: portion for portion in portions}
    for item in ingredients:
        if item.food_portion_id is None:
            continue
        portion = by_id.get(item.food_portion_id)
        if portion is None or portion.food_id != item.food_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"Ungültige Einheit für Lebensmittel-ID: {item.food_id}",
            )
    return by_id


def _commit(session: Session) -> None:
    try:
        session.commit()
    except SQLAlchemyError as error:
        session.rollback()
        raise _database_unavailable() from error


def _database_unavailable() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Rezeptverwaltung nicht verfügbar",
    )


def _serialize(recipe: Recipe) -> RecipeResponse:
    nutrition = calculate_recipe_nutrition(recipe)
    return RecipeResponse(
        id=recipe.id,
        title=recipe.title,
        servings=recipe.servings,
        is_meal_prep=recipe.servings > 1,
        meal_roles=[
            cast(MealRole, role.meal_role)
            for role in sorted(
                recipe.meal_roles,
                key=lambda item: MEAL_ROLE_ORDER.index(cast(MealRole, item.meal_role)),
            )
        ],
        ingredients=[
            RecipeIngredientResponse(
                food_id=item.food_id,
                food_name=item.food.name,
                food_portion_id=item.food_portion_id,
                amount=float(item.amount),
                unit=(item.food_portion.name if item.food_portion else item.food.base_unit),
                base_amount=float(
                    item.amount * item.food_portion.amount
                    if item.food_portion
                    else item.amount
                ),
                base_unit=cast(Literal["g", "ml"], item.food.base_unit),
                position=item.position,
            )
            for item in recipe.ingredients
        ],
        instructions=list(recipe.instructions),
        nutrition_total=_serialize_nutrients(nutrition.total),
        nutrition_per_serving=_serialize_nutrients(nutrition.per_serving),
        created_at=recipe.created_at,
        updated_at=recipe.updated_at,
    )


def _serialize_nutrients(nutrients: Nutrients) -> NutrientResponse:
    return NutrientResponse(
        calories_kcal=float(nutrients.calories_kcal),
        protein_g=float(nutrients.protein_g),
        carbohydrates_g=float(nutrients.carbohydrates_g),
        fat_g=float(nutrients.fat_g),
    )
