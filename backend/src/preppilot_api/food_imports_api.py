from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from preppilot_api.database import get_session
from preppilot_api.food_imports import (
    FoodImportNotFoundError,
    FoodImportPromotionError,
    PromoteFoodImportCommand,
    create_food_import,
    get_food_import,
    list_food_imports,
    promote_food_import,
)
from preppilot_api.food_sources import (
    FoodDataCentralSource,
    FoodSourceNotFoundError,
    FoodSourcePayloadError,
    FoodSourceUnavailableError,
    get_fooddata_central_source,
)
from preppilot_api.models import FoodImport

router = APIRouter(prefix="/api/internal/food-imports", tags=["food-imports"])
DatabaseSession = Annotated[Session, Depends(get_session)]
FoodDataCentralDependency = Annotated[
    FoodDataCentralSource, Depends(get_fooddata_central_source)
]


class FoodImportResponse(BaseModel):
    id: int
    source_name: str
    external_id: str
    fetched_at: str
    content_hash: str
    status: str
    candidate_name: str | None
    calories_per_100: Decimal | None
    protein_per_100: Decimal | None
    carbs_per_100: Decimal | None
    fat_per_100: Decimal | None
    review_reasons: list[str]
    raw_payload: dict[str, object]


class CreatedFoodImportResponse(BaseModel):
    created: bool
    food_import: FoodImportResponse


class PromotedFoodResponse(BaseModel):
    created: bool
    food_id: int
    catalog_key: str
    source_food_import_id: int


@router.get("", response_model=list[FoodImportResponse])
def read_food_imports(session: DatabaseSession) -> list[FoodImportResponse]:
    return [_serialize(item) for item in list_food_imports(session)]


@router.post(
    "/sources/fooddata-central/{fdc_id}",
    response_model=CreatedFoodImportResponse,
)
def import_fooddata_central_food(
    fdc_id: str,
    response: Response,
    session: DatabaseSession,
    source: FoodDataCentralDependency,
) -> CreatedFoodImportResponse:
    try:
        food_import, created = create_food_import(session, source.fetch(fdc_id))
        session.commit()
    except FoodSourceNotFoundError as error:
        session.rollback()
        raise HTTPException(
            status_code=404, detail="FoodData-Central-Lebensmittel nicht gefunden"
        ) from error
    except FoodSourcePayloadError as error:
        session.rollback()
        raise HTTPException(status_code=422, detail=str(error)) from error
    except FoodSourceUnavailableError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="FoodData Central nicht erreichbar",
        ) from error
    except SQLAlchemyError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Importdatenbank nicht verfügbar",
        ) from error
    response.status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    return CreatedFoodImportResponse(
        created=created, food_import=_serialize(food_import)
    )


@router.get("/{food_import_id}", response_model=FoodImportResponse)
def read_food_import(
    food_import_id: int, session: DatabaseSession
) -> FoodImportResponse:
    try:
        return _serialize(get_food_import(session, food_import_id))
    except FoodImportNotFoundError as error:
        raise HTTPException(
            status_code=404, detail="Lebensmittelimport nicht gefunden"
        ) from error


@router.post("/{food_import_id}/promote", response_model=PromotedFoodResponse)
def promote_reviewed_food_import(
    food_import_id: int,
    command: PromoteFoodImportCommand,
    session: DatabaseSession,
) -> PromotedFoodResponse:
    try:
        food, created = promote_food_import(session, food_import_id, command)
        session.commit()
    except FoodImportNotFoundError as error:
        session.rollback()
        raise HTTPException(
            status_code=404, detail="Lebensmittelimport nicht gefunden"
        ) from error
    except FoodImportPromotionError as error:
        session.rollback()
        raise HTTPException(status_code=422, detail=str(error)) from error
    except SQLAlchemyError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Lebensmittelkatalog nicht verfügbar",
        ) from error
    return PromotedFoodResponse(
        created=created,
        food_id=food.id,
        catalog_key=food.catalog_key,
        source_food_import_id=food_import_id,
    )


def _serialize(food_import: FoodImport) -> FoodImportResponse:
    return FoodImportResponse(
        id=food_import.id,
        source_name=food_import.source_name,
        external_id=food_import.external_id,
        fetched_at=food_import.fetched_at.isoformat(),
        content_hash=food_import.content_hash,
        status=food_import.status.value,
        candidate_name=food_import.candidate_name,
        calories_per_100=food_import.calories_per_100,
        protein_per_100=food_import.protein_per_100,
        carbs_per_100=food_import.carbs_per_100,
        fat_per_100=food_import.fat_per_100,
        review_reasons=food_import.review_reasons,
        raw_payload=food_import.raw_payload,
    )
