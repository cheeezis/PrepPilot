from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal, cast

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from preppilot_api.database import get_session
from preppilot_api.models import Food, RecipeIngredient

router = APIRouter(prefix="/api/foods", tags=["foods"])
DatabaseSession = Annotated[Session, Depends(get_session)]
FoodCategory = Literal[
    "protein",
    "carbohydrate",
    "vegetable",
    "dairy",
    "fat",
    "sauce",
    "spice",
    "other",
]


class FoodWriteRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    base_unit: Literal["g", "ml"]
    category: FoodCategory
    calories_kcal: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    protein_g: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    carbohydrates_g: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    fat_g: Decimal = Field(ge=0, max_digits=10, decimal_places=2)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = " ".join(value.split())
        if not normalized:
            raise ValueError("name must not be blank")
        return normalized


class FoodResponse(BaseModel):
    id: int
    name: str
    base_unit: Literal["g", "ml"]
    category: FoodCategory
    calories_kcal: float
    protein_g: float
    carbohydrates_g: float
    fat_g: float
    created_at: datetime
    updated_at: datetime


@router.get("", response_model=list[FoodResponse])
def list_foods(session: DatabaseSession) -> list[FoodResponse]:
    try:
        foods = session.scalars(select(Food).order_by(func.lower(Food.name), Food.id))
    except SQLAlchemyError as error:
        raise _database_unavailable() from error
    return [_serialize(food) for food in foods]


@router.post("", response_model=FoodResponse, status_code=status.HTTP_201_CREATED)
def create_food(request: FoodWriteRequest, session: DatabaseSession) -> FoodResponse:
    food = Food()
    _apply_request(food, request)
    session.add(food)
    _commit(session, duplicate_detail="Ein Lebensmittel mit diesem Namen existiert bereits")
    session.refresh(food)
    return _serialize(food)


@router.put("/{food_id}", response_model=FoodResponse)
def update_food(
    food_id: int, request: FoodWriteRequest, session: DatabaseSession
) -> FoodResponse:
    food = session.get(Food, food_id)
    if food is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lebensmittel nicht gefunden",
        )
    _apply_request(food, request)
    _commit(session, duplicate_detail="Ein Lebensmittel mit diesem Namen existiert bereits")
    session.refresh(food)
    return _serialize(food)


@router.delete("/{food_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_food(food_id: int, session: DatabaseSession) -> Response:
    food = session.get(Food, food_id)
    if food is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lebensmittel nicht gefunden",
        )
    if session.scalar(
        select(RecipeIngredient.id).where(RecipeIngredient.food_id == food_id).limit(1)
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Lebensmittel wird bereits in einem Rezept verwendet",
        )
    session.delete(food)
    _commit(
        session,
        duplicate_detail="Lebensmittel wird bereits in einem Rezept verwendet",
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _apply_request(food: Food, request: FoodWriteRequest) -> None:
    food.name = request.name
    food.base_unit = request.base_unit
    food.category = request.category
    food.calories_kcal = request.calories_kcal
    food.protein_g = request.protein_g
    food.carbohydrates_g = request.carbohydrates_g
    food.fat_g = request.fat_g


def _commit(session: Session, duplicate_detail: str) -> None:
    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=duplicate_detail,
        ) from error
    except SQLAlchemyError as error:
        session.rollback()
        raise _database_unavailable() from error


def _database_unavailable() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Lebensmittelkatalog nicht verfügbar",
    )


def _serialize(food: Food) -> FoodResponse:
    return FoodResponse(
        id=food.id,
        name=food.name,
        base_unit=cast(Literal["g", "ml"], food.base_unit),
        category=cast(FoodCategory, food.category),
        calories_kcal=float(food.calories_kcal),
        protein_g=float(food.protein_g),
        carbohydrates_g=float(food.carbohydrates_g),
        fat_g=float(food.fat_g),
        created_at=food.created_at,
        updated_at=food.updated_at,
    )
