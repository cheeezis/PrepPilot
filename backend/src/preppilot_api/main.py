from decimal import Decimal
from typing import Literal, Mapping

from fastapi import FastAPI, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError

from preppilot_api.catalog_data import FoodDefinition, load_catalog
from preppilot_api.database import check_database_connection
from preppilot_api.nutrition import Nutrients
from preppilot_api.planner import DayPlan, PlanTargets, generate_day_plans


class HealthResponse(BaseModel):
    status: Literal["ok", "error"]
    database: Literal["ok", "unavailable"]


class DayPlanRequest(BaseModel):
    calories: Decimal = Field(gt=0)
    protein_minimum: Decimal = Field(gt=0)
    fat_maximum: Decimal = Field(gt=0)
    carbs: Decimal = Field(gt=0)
    meal_count: int = Field(ge=3, le=6)


class NutrientValuesResponse(BaseModel):
    calories: float
    protein: float
    carbs: float
    fat: float


class IngredientResponse(BaseModel):
    food_key: str
    name: str
    amount: float
    unit: Literal["g", "ml"]


class PlannedMealResponse(BaseModel):
    key: str
    name: str
    role: str
    portion_factor: float
    nutrients: NutrientValuesResponse
    ingredients: list[IngredientResponse]


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
    meals: list[PlannedMealResponse]


class DayPlansResponse(BaseModel):
    outcome: Literal["plans_found", "approximations_only", "no_usable_plan"]
    plans: list[DayPlanResponse]


app = FastAPI(title="PrepPilot API", version="0.1.0")


@app.get("/api/health", tags=["system"], response_model=HealthResponse)
def health(response: Response) -> HealthResponse:
    try:
        check_database_connection()
    except SQLAlchemyError:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return HealthResponse(status="error", database="unavailable")

    return HealthResponse(status="ok", database="ok")


@app.post(
    "/api/day-plans",
    tags=["planning"],
    response_model=DayPlansResponse,
)
def create_day_plans(request: DayPlanRequest) -> DayPlansResponse:
    catalog = load_catalog()
    targets = PlanTargets(
        calories=request.calories,
        protein_minimum=request.protein_minimum,
        fat_maximum=request.fat_maximum,
        carbs=request.carbs,
        meal_count=request.meal_count,
    )
    foods = {food.key: food for food in catalog.foods}
    plans = generate_day_plans(targets, catalog)
    return DayPlansResponse(
        outcome=(
            "no_usable_plan"
            if not plans
            else "plans_found"
            if any(plan.status == "valid" for plan in plans)
            else "approximations_only"
        ),
        plans=[
            _serialize_day_plan(plan, foods)
            for plan in plans
        ]
    )


def _serialize_day_plan(
    plan: DayPlan, foods: Mapping[str, FoodDefinition]
) -> DayPlanResponse:
    return DayPlanResponse(
        status=plan.status,
        score=float(plan.score),
        nutrients=_serialize_nutrients(plan.nutrients),
        evaluations=[
            RuleEvaluationResponse(
                metric=evaluation.metric,
                kind=evaluation.kind,
                actual=float(evaluation.actual),
                target=_optional_float(evaluation.target),
                minimum=_optional_float(evaluation.minimum),
                maximum=_optional_float(evaluation.maximum),
                satisfied=evaluation.satisfied,
            )
            for evaluation in plan.evaluations
        ],
        meals=[
            PlannedMealResponse(
                key=planned_meal.meal.key,
                name=planned_meal.meal.name,
                role=planned_meal.role.value,
                portion_factor=float(planned_meal.portion_factor),
                nutrients=_serialize_nutrients(planned_meal.nutrients),
                ingredients=[
                    IngredientResponse(
                        food_key=ingredient.food_key,
                        name=foods[ingredient.food_key].name,
                        amount=float(
                            ingredient.amount * planned_meal.portion_factor
                        ),
                        unit=foods[ingredient.food_key].unit.value,
                    )
                    for ingredient in planned_meal.meal.ingredients
                ],
            )
            for planned_meal in plan.meals
        ],
    )


def _serialize_nutrients(nutrients: Nutrients) -> NutrientValuesResponse:
    return NutrientValuesResponse(
        calories=float(nutrients.calories),
        protein=float(nutrients.protein),
        carbs=float(nutrients.carbs),
        fat=float(nutrients.fat),
    )


def _optional_float(value: Decimal | None) -> float | None:
    return None if value is None else float(value)
