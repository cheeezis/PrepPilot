from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Annotated, Literal, cast

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from preppilot_api.database import get_session
from preppilot_api.models import MealAssignment, Recipe, WeeklyPlan
from preppilot_api.weekly_planner import PlanGenerationError, generate_assignments

router = APIRouter(prefix="/api/weekly-plans", tags=["weekly plans"])
DatabaseSession = Annotated[Session, Depends(get_session)]
MealRole = Literal["breakfast", "lunch", "dinner", "snack"]
MEAL_ROLE_ORDER = {"breakfast": 0, "lunch": 1, "dinner": 2, "snack": 3}


class GenerateWeeklyPlanRequest(BaseModel):
    start_date: date
    snacks_per_day: int = Field(ge=0, le=3)
    calories_target_kcal: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    protein_minimum_g: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    carbohydrates_target_g: Decimal = Field(
        ge=0, max_digits=10, decimal_places=2
    )
    fat_maximum_g: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    replace_existing: bool = False


class MealAssignmentResponse(BaseModel):
    id: int
    date: date
    day_index: int
    meal_role: MealRole
    slot_number: int
    recipe_id: int
    recipe_title: str
    portion_number: int | None
    recipe_servings: int


class WeeklyPlanResponse(BaseModel):
    id: int
    start_date: date
    end_date: date
    snacks_per_day: int
    calories_target_kcal: float
    protein_minimum_g: float
    carbohydrates_target_g: float
    fat_maximum_g: float
    assignments: list[MealAssignmentResponse]
    created_at: datetime
    updated_at: datetime


@router.get("", response_model=list[WeeklyPlanResponse])
def list_weekly_plans(session: DatabaseSession) -> list[WeeklyPlanResponse]:
    try:
        plans = session.scalars(
            select(WeeklyPlan).order_by(WeeklyPlan.start_date.desc(), WeeklyPlan.id)
        ).all()
    except SQLAlchemyError as error:
        raise _database_unavailable() from error
    return [_serialize(plan) for plan in plans]


@router.get("/{plan_id}", response_model=WeeklyPlanResponse)
def get_weekly_plan(plan_id: int, session: DatabaseSession) -> WeeklyPlanResponse:
    return _serialize(_get_plan(plan_id, session))


@router.post(
    "/generate",
    response_model=WeeklyPlanResponse,
    status_code=status.HTTP_201_CREATED,
)
def generate_weekly_plan(
    request: GenerateWeeklyPlanRequest, session: DatabaseSession
) -> WeeklyPlanResponse:
    end_date = request.start_date + timedelta(days=6)
    overlapping = _overlapping_plans(request.start_date, end_date, session)
    if overlapping:
        exact = [
            plan
            for plan in overlapping
            if plan.start_date == request.start_date and plan.end_date == end_date
        ]
        if not request.replace_existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Für diesen Zeitraum existiert bereits ein Wochenplan",
            )
        if len(exact) != len(overlapping):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Der Zeitraum überschneidet sich mit einem anderen Wochenplan",
            )
        for plan in exact:
            session.delete(plan)
        session.flush()

    try:
        recipes = list(session.scalars(select(Recipe).order_by(Recipe.id)).all())
        assignments = generate_assignments(recipes, request.snacks_per_day)
    except PlanGenerationError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error
    except SQLAlchemyError as error:
        session.rollback()
        raise _database_unavailable() from error

    plan = WeeklyPlan(
        start_date=request.start_date,
        end_date=end_date,
        snacks_per_day=request.snacks_per_day,
        calories_target_kcal=request.calories_target_kcal,
        protein_minimum_g=request.protein_minimum_g,
        carbohydrates_target_g=request.carbohydrates_target_g,
        fat_maximum_g=request.fat_maximum_g,
        assignments=assignments,
    )
    session.add(plan)
    _commit(session)
    session.refresh(plan)
    return _serialize(plan)


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_weekly_plan(plan_id: int, session: DatabaseSession) -> Response:
    session.delete(_get_plan(plan_id, session))
    _commit(session)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _get_plan(plan_id: int, session: Session) -> WeeklyPlan:
    try:
        plan = session.get(WeeklyPlan, plan_id)
    except SQLAlchemyError as error:
        raise _database_unavailable() from error
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wochenplan nicht gefunden",
        )
    return plan


def _overlapping_plans(
    start_date: date, end_date: date, session: Session
) -> list[WeeklyPlan]:
    try:
        return list(
            session.scalars(
                select(WeeklyPlan).where(
                    WeeklyPlan.start_date <= end_date,
                    WeeklyPlan.end_date >= start_date,
                )
            ).all()
        )
    except SQLAlchemyError as error:
        raise _database_unavailable() from error


def _commit(session: Session) -> None:
    try:
        session.commit()
    except SQLAlchemyError as error:
        session.rollback()
        raise _database_unavailable() from error


def _database_unavailable() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Wochenplanung nicht verfügbar",
    )


def _serialize(plan: WeeklyPlan) -> WeeklyPlanResponse:
    return WeeklyPlanResponse(
        id=plan.id,
        start_date=plan.start_date,
        end_date=plan.end_date,
        snacks_per_day=plan.snacks_per_day,
        calories_target_kcal=float(plan.calories_target_kcal),
        protein_minimum_g=float(plan.protein_minimum_g),
        carbohydrates_target_g=float(plan.carbohydrates_target_g),
        fat_maximum_g=float(plan.fat_maximum_g),
        assignments=[
            _serialize_assignment(plan, item)
            for item in sorted(
                plan.assignments,
                key=lambda assignment: (
                    assignment.day_index,
                    MEAL_ROLE_ORDER[assignment.meal_role],
                    assignment.slot_number,
                ),
            )
        ],
        created_at=plan.created_at,
        updated_at=plan.updated_at,
    )


def _serialize_assignment(
    plan: WeeklyPlan, assignment: MealAssignment
) -> MealAssignmentResponse:
    return MealAssignmentResponse(
        id=assignment.id,
        date=plan.start_date + timedelta(days=assignment.day_index),
        day_index=assignment.day_index,
        meal_role=cast(MealRole, assignment.meal_role),
        slot_number=assignment.slot_number,
        recipe_id=assignment.recipe_id,
        recipe_title=assignment.recipe.title,
        portion_number=assignment.portion_number,
        recipe_servings=assignment.recipe.servings,
    )
