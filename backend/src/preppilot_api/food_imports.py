import hashlib
import json
from datetime import UTC, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from preppilot_api.models import (
    Food,
    FoodImport,
    FoodImportStatus,
    FoodOrigin,
    MeasurementUnit,
)


class FoodImportModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class CreateFoodImportCommand(FoodImportModel):
    source_name: str = Field(min_length=1, max_length=100)
    external_id: str = Field(min_length=1, max_length=200)
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    raw_payload: dict[str, object]
    candidate_name: str | None = None
    calories_per_100: Decimal | None = Field(default=None, ge=0)
    protein_per_100: Decimal | None = Field(default=None, ge=0)
    carbs_per_100: Decimal | None = Field(default=None, ge=0)
    fat_per_100: Decimal | None = Field(default=None, ge=0)
    review_reasons: tuple[str, ...] = ()


class PromoteFoodImportCommand(FoodImportModel):
    catalog_key: str = Field(pattern=r"^[a-z0-9_]+$")
    name: str = Field(min_length=1, max_length=200)


class FoodImportNotFoundError(LookupError):
    pass


class FoodImportPromotionError(ValueError):
    pass


def create_food_import(
    session: Session, command: CreateFoodImportCommand
) -> tuple[FoodImport, bool]:
    content_hash = _content_hash(command.raw_payload)
    existing = session.scalar(
        select(FoodImport).where(
            FoodImport.source_name == command.source_name.strip(),
            FoodImport.external_id == command.external_id.strip(),
            FoodImport.content_hash == content_hash,
        )
    )
    if existing is not None:
        return existing, False

    complete = (
        command.candidate_name is not None
        and command.calories_per_100 is not None
        and command.protein_per_100 is not None
        and command.carbs_per_100 is not None
        and command.fat_per_100 is not None
        and not command.review_reasons
    )
    food_import = FoodImport(
        source_name=command.source_name.strip(),
        external_id=command.external_id.strip(),
        fetched_at=command.fetched_at,
        raw_payload=command.raw_payload,
        content_hash=content_hash,
        status=(
            FoodImportStatus.READY_FOR_CATALOG_REVIEW
            if complete
            else FoodImportStatus.NEEDS_REVIEW
        ),
        candidate_name=command.candidate_name,
        calories_per_100=command.calories_per_100,
        protein_per_100=command.protein_per_100,
        carbs_per_100=command.carbs_per_100,
        fat_per_100=command.fat_per_100,
        review_reasons=list(command.review_reasons),
    )
    session.add(food_import)
    session.flush()
    return food_import, True


def promote_food_import(
    session: Session,
    food_import_id: int,
    command: PromoteFoodImportCommand,
) -> tuple[Food, bool]:
    food_import = get_food_import(session, food_import_id)
    existing = session.scalar(
        select(Food).where(Food.source_food_import_id == food_import.id)
    )
    if existing is not None:
        return existing, False
    if food_import.status != FoodImportStatus.READY_FOR_CATALOG_REVIEW:
        raise FoodImportPromotionError("food import is not ready for catalog review")
    values = (
        food_import.calories_per_100,
        food_import.protein_per_100,
        food_import.carbs_per_100,
        food_import.fat_per_100,
    )
    if any(value is None for value in values):
        raise FoodImportPromotionError("food import contains incomplete nutrients")
    if session.scalar(select(Food.id).where(Food.catalog_key == command.catalog_key)):
        raise FoodImportPromotionError("catalog key already exists")

    food = Food(
        catalog_key=command.catalog_key,
        name=command.name.strip(),
        brand=None,
        unit=MeasurementUnit.GRAM,
        calories_per_100=food_import.calories_per_100,
        protein_per_100=food_import.protein_per_100,
        carbs_per_100=food_import.carbs_per_100,
        fat_per_100=food_import.fat_per_100,
        source_name="USDA FoodData Central",
        source_reference=(
            "https://fdc.nal.usda.gov/fdc-app.html#/food-details/"
            f"{food_import.external_id}/nutrients"
        ),
        origin=FoodOrigin.FOOD_IMPORT,
        source_food_import_id=food_import.id,
    )
    session.add(food)
    session.flush()
    return food, True


def get_food_import(session: Session, food_import_id: int) -> FoodImport:
    food_import = session.get(FoodImport, food_import_id)
    if food_import is None:
        raise FoodImportNotFoundError(food_import_id)
    return food_import


def list_food_imports(session: Session) -> tuple[FoodImport, ...]:
    return tuple(session.scalars(select(FoodImport).order_by(FoodImport.id)))


def _content_hash(raw_payload: dict[str, object]) -> str:
    serialized = json.dumps(
        raw_payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
