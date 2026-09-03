from decimal import Decimal
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from preppilot_api.database import get_session
from preppilot_api.nhs_import import ImportItem, import_nhs_recipes
from preppilot_api.nutrition import Nutrients
from preppilot_api.planner import DayPlan, PlanTargets, generate_day_plans
from preppilot_api.recipe_repository import (
    RecipeCatalogUnavailableError,
    RecipeDefinition,
    load_recipes,
)


class HealthResponse(BaseModel):
    status: Literal["ok", "error"]
    database: Literal["ok", "unavailable"]
    recipes: Literal["ok", "unavailable"]


class DayPlanRequest(BaseModel):
    calories: Decimal = Field(gt=0)
    protein_minimum: Decimal = Field(gt=0)
    fat_maximum: Decimal = Field(gt=0)
    carbs: Decimal = Field(gt=0)


class NutrientValuesResponse(BaseModel):
    calories: float
    protein: float
    carbs: float
    fat: float
    sugar: float | None
    saturated_fat: float | None
    fiber: float | None
    salt: float | None


class PlannedRecipeResponse(BaseModel):
    id: int
    title: str
    category: Literal["breakfast", "lunch", "dinner"]
    portions: int
    recipe_servings: int
    source_url: str
    license_name: str
    attribution_text: str
    nutrients: NutrientValuesResponse
    ingredients: list[str]
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
    category: Literal["breakfast", "lunch", "dinner"]
    servings: int
    source_url: str
    license_name: str
    attribution_text: str
    nutrients: NutrientValuesResponse
    ingredients: list[str]
    instructions: list[str]


class ImportItemResponse(BaseModel):
    source_url: str
    status: Literal["created", "updated", "unchanged", "rejected"]
    title: str | None
    reason: str | None


class ImportRunResponse(BaseModel):
    created: int
    updated: int
    unchanged: int
    rejected: int
    items: list[ImportItemResponse]


app = FastAPI(title="PrepPilot API", version="0.2.0")
DatabaseSession = Annotated[Session, Depends(get_session)]


@app.get("/api/health", tags=["system"], response_model=HealthResponse)
def health(response: Response, session: DatabaseSession) -> HealthResponse:
    try:
        load_recipes(session)
    except SQLAlchemyError:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return HealthResponse(
            status="error", database="unavailable", recipes="unavailable"
        )
    except RecipeCatalogUnavailableError:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return HealthResponse(status="error", database="ok", recipes="unavailable")
    return HealthResponse(status="ok", database="ok", recipes="ok")


@app.get("/api/recipes", tags=["recipes"], response_model=list[RecipeResponse])
def list_recipes(session: DatabaseSession) -> list[RecipeResponse]:
    try:
        recipes = load_recipes(session)
    except (SQLAlchemyError, RecipeCatalogUnavailableError) as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Rezeptbestand nicht verfügbar",
        ) from error
    return [_serialize_recipe(recipe) for recipe in recipes]


@app.post(
    "/api/imports/nhs",
    tags=["imports"],
    response_model=ImportRunResponse,
)
def run_nhs_import(session: DatabaseSession) -> ImportRunResponse:
    try:
        items = import_nhs_recipes(session)
    except SQLAlchemyError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Rezeptimport konnte nicht gespeichert werden",
        ) from error
    return _serialize_import_run(items)


@app.post("/api/day-plans", tags=["planning"], response_model=DayPlansResponse)
def create_day_plans(
    request: DayPlanRequest, session: DatabaseSession
) -> DayPlansResponse:
    try:
        recipes = load_recipes(session)
    except (SQLAlchemyError, RecipeCatalogUnavailableError) as error:
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
        category=recipe.category,
        servings=recipe.servings,
        source_url=recipe.source_url,
        license_name=recipe.license_name,
        attribution_text=recipe.attribution_text,
        nutrients=_serialize_nutrients(recipe.nutrients),
        ingredients=list(recipe.ingredients),
        instructions=list(recipe.instructions),
    )


def _serialize_import_run(items: tuple[ImportItem, ...]) -> ImportRunResponse:
    return ImportRunResponse(
        created=sum(item.status == "created" for item in items),
        updated=sum(item.status == "updated" for item in items),
        unchanged=sum(item.status == "unchanged" for item in items),
        rejected=sum(item.status == "rejected" for item in items),
        items=[ImportItemResponse(**item.__dict__) for item in items],
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
                category=item.recipe.category,
                portions=item.portions,
                recipe_servings=item.recipe.servings,
                source_url=item.recipe.source_url,
                license_name=item.recipe.license_name,
                attribution_text=item.recipe.attribution_text,
                nutrients=_serialize_nutrients(item.nutrients),
                ingredients=list(item.recipe.ingredients),
                instructions=list(item.recipe.instructions),
            )
            for item in plan.recipes
        ],
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
