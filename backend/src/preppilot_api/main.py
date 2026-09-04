from decimal import Decimal
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, HTTPException, Response, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from preppilot_api.database import get_session
from preppilot_api.nutrition import Nutrients
from preppilot_api.planner import DayPlan, PlanTargets, generate_day_plans
from preppilot_api.recipe_repository import (
    RecipeCategory,
    RecipeDefinition,
    RecipeIngredient,
    RecipeValues,
    create_recipe,
    delete_recipe,
    load_recipes,
    update_recipe,
)


class HealthResponse(BaseModel):
    status: Literal["ok", "error"]
    database: Literal["ok", "unavailable"]
    recipes: Literal["ok", "empty", "unavailable"]


def _default_meal_categories() -> list[RecipeCategory]:
    return ["breakfast", "lunch", "dinner"]


class DayPlanRequest(BaseModel):
    calories: Decimal = Field(gt=0)
    protein_minimum: Decimal = Field(gt=0)
    fat_maximum: Decimal = Field(gt=0)
    carbs: Decimal = Field(gt=0)
    meal_categories: list[RecipeCategory] = Field(
        default_factory=_default_meal_categories,
        min_length=1,
        max_length=4,
    )

    @field_validator("meal_categories")
    @classmethod
    def meal_categories_must_be_unique(
        cls, value: list[RecipeCategory]
    ) -> list[RecipeCategory]:
        if len(set(value)) != len(value):
            raise ValueError("meal categories must be unique")
        return value


class NutrientValuesResponse(BaseModel):
    calories: float
    protein: float
    carbs: float
    fat: float
    sugar: float | None
    saturated_fat: float | None
    fiber: float | None
    salt: float | None


class RecipeIngredientResponse(BaseModel):
    amount: float
    unit: str
    name: str


class PlannedRecipeResponse(BaseModel):
    id: int
    title: str
    category: Literal["breakfast", "lunch", "dinner", "snack"]
    recipe_servings: int
    source_url: str | None
    nutrients: NutrientValuesResponse
    ingredients: list[RecipeIngredientResponse]
    instructions: list[str]


class RuleEvaluationResponse(BaseModel):
    metric: Literal["calories", "protein", "fat", "carbs"]
    kind: Literal["hard", "soft"]
    actual: float
    target: float | None
    minimum: float | None
    maximum: float | None
    satisfied: bool


class DayPlanResponse(BaseModel):
    status: Literal["valid", "approximation"]
    score: float
    nutrients: NutrientValuesResponse
    evaluations: list[RuleEvaluationResponse]
    recipes: list[PlannedRecipeResponse]


class DayPlansResponse(BaseModel):
    outcome: Literal["plans_found", "approximations_only", "no_usable_plan"]
    plans: list[DayPlanResponse]


class RecipeResponse(BaseModel):
    id: int
    title: str
    categories: list[Literal["breakfast", "lunch", "dinner", "snack"]]
    servings: int
    source_url: str | None
    preparation_minutes: int | None
    cooking_minutes: int | None
    nutrients: NutrientValuesResponse
    ingredients: list[RecipeIngredientResponse]
    instructions: list[str]


class RecipeIngredientRequest(BaseModel):
    amount: Decimal = Field(gt=0)
    unit: str = Field(min_length=1, max_length=40)
    name: str = Field(min_length=1, max_length=200)

    @field_validator("unit", "name")
    @classmethod
    def text_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("ingredient text must not be blank")
        return value


class RecipeWriteRequest(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    categories: list[RecipeCategory] = Field(min_length=1, max_length=4)
    servings: int = Field(gt=0)
    calories_per_serving: Decimal = Field(gt=0)
    protein_per_serving: Decimal = Field(ge=0)
    carbs_per_serving: Decimal = Field(ge=0)
    fat_per_serving: Decimal = Field(ge=0)
    sugar_per_serving: Decimal | None = Field(default=None, ge=0)
    saturated_fat_per_serving: Decimal | None = Field(default=None, ge=0)
    fiber_per_serving: Decimal | None = Field(default=None, ge=0)
    salt_per_serving: Decimal | None = Field(default=None, ge=0)
    ingredients: list[RecipeIngredientRequest] = Field(min_length=1)
    instructions: list[str] = Field(min_length=1)
    preparation_minutes: int | None = Field(default=None, ge=0)
    cooking_minutes: int | None = Field(default=None, ge=0)
    source_url: str | None = None

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("title must not be blank")
        return value

    @field_validator("categories")
    @classmethod
    def categories_must_be_unique(
        cls, value: list[RecipeCategory]
    ) -> list[RecipeCategory]:
        if len(set(value)) != len(value):
            raise ValueError("categories must be unique")
        return value

    @field_validator("instructions")
    @classmethod
    def text_items_must_not_be_blank(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value]
        if any(not item for item in cleaned):
            raise ValueError("items must not be blank")
        return cleaned

    @field_validator("source_url")
    @classmethod
    def empty_source_url_becomes_none(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None


app = FastAPI(title="PrepPilot API", version="0.2.0")
DatabaseSession = Annotated[Session, Depends(get_session)]


@app.get("/api/health", tags=["system"], response_model=HealthResponse)
def health(response: Response, session: DatabaseSession) -> HealthResponse:
    try:
        recipes = load_recipes(session)
    except SQLAlchemyError:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return HealthResponse(
            status="error", database="unavailable", recipes="unavailable"
        )
    return HealthResponse(
        status="ok",
        database="ok",
        recipes="ok" if recipes else "empty",
    )


@app.get("/api/recipes", tags=["recipes"], response_model=list[RecipeResponse])
def list_recipes(session: DatabaseSession) -> list[RecipeResponse]:
    try:
        recipes = load_recipes(session)
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Rezeptbestand nicht verfügbar",
        ) from error
    return [_serialize_recipe(recipe) for recipe in recipes]


@app.post(
    "/api/recipes",
    tags=["recipes"],
    response_model=RecipeResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_recipe(
    request: RecipeWriteRequest, session: DatabaseSession
) -> RecipeResponse:
    try:
        recipe = create_recipe(session, _recipe_values(request))
    except SQLAlchemyError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Rezept konnte nicht gespeichert werden",
        ) from error
    return _serialize_recipe(recipe)


@app.put("/api/recipes/{recipe_id}", tags=["recipes"], response_model=RecipeResponse)
def edit_recipe(
    recipe_id: int, request: RecipeWriteRequest, session: DatabaseSession
) -> RecipeResponse:
    try:
        recipe = update_recipe(session, recipe_id, _recipe_values(request))
    except SQLAlchemyError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Rezept konnte nicht gespeichert werden",
        ) from error
    if recipe is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return _serialize_recipe(recipe)


@app.delete(
    "/api/recipes/{recipe_id}",
    tags=["recipes"],
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_recipe(recipe_id: int, session: DatabaseSession) -> Response:
    try:
        deleted = delete_recipe(session, recipe_id)
    except SQLAlchemyError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Rezept konnte nicht gelöscht werden",
        ) from error
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post("/api/day-plans", tags=["planning"], response_model=DayPlansResponse)
def create_day_plans(
    request: DayPlanRequest, session: DatabaseSession
) -> DayPlansResponse:
    try:
        recipes = load_recipes(session)
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Rezeptbestand nicht verfügbar",
        ) from error
    plans = generate_day_plans(
        PlanTargets(
            calories=request.calories,
            protein_minimum=request.protein_minimum,
            fat_maximum=request.fat_maximum,
            carbs=request.carbs,
        ),
        recipes,
        tuple(request.meal_categories),
    )
    return DayPlansResponse(
        outcome=(
            "no_usable_plan"
            if not plans
            else "plans_found"
            if any(plan.status == "valid" for plan in plans)
            else "approximations_only"
        ),
        plans=[_serialize_day_plan(plan) for plan in plans],
    )


def _serialize_recipe(recipe: RecipeDefinition) -> RecipeResponse:
    return RecipeResponse(
        id=recipe.id,
        title=recipe.title,
        categories=list(recipe.categories),
        servings=recipe.servings,
        source_url=recipe.source_url,
        preparation_minutes=recipe.preparation_minutes,
        cooking_minutes=recipe.cooking_minutes,
        nutrients=_serialize_nutrients(recipe.nutrients),
        ingredients=[_serialize_ingredient(item) for item in recipe.ingredients],
        instructions=list(recipe.instructions),
    )


def _serialize_day_plan(plan: DayPlan) -> DayPlanResponse:
    return DayPlanResponse(
        status=plan.status,
        score=float(plan.score),
        nutrients=_serialize_nutrients(plan.nutrients),
        evaluations=[
            RuleEvaluationResponse(
                metric=item.metric,
                kind=item.kind,
                actual=float(item.actual),
                target=_optional_float(item.target),
                minimum=_optional_float(item.minimum),
                maximum=_optional_float(item.maximum),
                satisfied=item.satisfied,
            )
            for item in plan.evaluations
        ],
        recipes=[
            PlannedRecipeResponse(
                id=item.recipe.id,
                title=item.recipe.title,
                category=item.category,
                recipe_servings=item.recipe.servings,
                source_url=item.recipe.source_url,
                nutrients=_serialize_nutrients(item.nutrients),
                ingredients=[
                    _serialize_ingredient(ingredient)
                    for ingredient in item.recipe.ingredients
                ],
                instructions=list(item.recipe.instructions),
            )
            for item in plan.recipes
        ],
    )


def _recipe_values(request: RecipeWriteRequest) -> RecipeValues:
    return RecipeValues(
        title=request.title,
        categories=tuple(request.categories),
        servings=request.servings,
        source_url=request.source_url,
        ingredients=tuple(
            RecipeIngredient(
                amount=ingredient.amount,
                unit=ingredient.unit,
                name=ingredient.name,
            )
            for ingredient in request.ingredients
        ),
        instructions=tuple(request.instructions),
        preparation_minutes=request.preparation_minutes,
        cooking_minutes=request.cooking_minutes,
        nutrients=Nutrients(
            calories=request.calories_per_serving,
            protein=request.protein_per_serving,
            carbs=request.carbs_per_serving,
            fat=request.fat_per_serving,
            sugar=request.sugar_per_serving,
            saturated_fat=request.saturated_fat_per_serving,
            fiber=request.fiber_per_serving,
            salt=request.salt_per_serving,
        ),
    )


def _serialize_ingredient(
    ingredient: RecipeIngredient,
) -> RecipeIngredientResponse:
    return RecipeIngredientResponse(
        amount=float(ingredient.amount),
        unit=ingredient.unit,
        name=ingredient.name,
    )


def _serialize_nutrients(nutrients: Nutrients) -> NutrientValuesResponse:
    return NutrientValuesResponse(
        calories=float(nutrients.calories),
        protein=float(nutrients.protein),
        carbs=float(nutrients.carbs),
        fat=float(nutrients.fat),
        sugar=_optional_float(nutrients.sugar),
        saturated_fat=_optional_float(nutrients.saturated_fat),
        fiber=_optional_float(nutrients.fiber),
        salt=_optional_float(nutrients.salt),
    )


def _optional_float(value: Decimal | None) -> float | None:
    return None if value is None else float(value)
