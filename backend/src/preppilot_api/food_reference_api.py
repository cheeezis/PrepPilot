from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from preppilot_api.database import get_session
from preppilot_api.food_reference import (
    FoodReferenceDataset,
    FoodReferencePayloadError,
    FoodReferenceSource,
    FoodReferenceUnavailableError,
    get_food_reference_source,
    import_food_references,
    parse_food_reference_archive,
)
from preppilot_api.food_sources import FoodSearchCandidate
from preppilot_api.food_suggestions import suggest_food
from preppilot_api.models import FoodReferenceItem

router = APIRouter(prefix="/api/internal/food-references", tags=["food-references"])
DatabaseSession = Annotated[Session, Depends(get_session)]
FoodReferenceDependency = Annotated[
    FoodReferenceSource, Depends(get_food_reference_source)
]


class FoodReferenceImportResponse(BaseModel):
    dataset: str
    parsed: int
    created: int
    updated: int
    unchanged: int
    complete: int


class FoodReferenceStatsResponse(BaseModel):
    total: int
    complete: int
    by_data_type: dict[str, int]


class FoodReferenceSearchResult(BaseModel):
    fdc_id: str
    description: str
    data_type: str
    score: int
    calories_per_100: Decimal | None
    protein_per_100: Decimal | None
    carbs_per_100: Decimal | None
    fat_per_100: Decimal | None


@router.post(
    "/sources/fooddata-central/{dataset}",
    response_model=FoodReferenceImportResponse,
)
def import_fooddata_central_reference(
    dataset: FoodReferenceDataset,
    session: DatabaseSession,
    source: FoodReferenceDependency,
) -> FoodReferenceImportResponse:
    try:
        records = parse_food_reference_archive(source.download(dataset), dataset)
        result = import_food_references(session, dataset, records)
        session.commit()
    except FoodReferencePayloadError as error:
        session.rollback()
        raise HTTPException(status_code=422, detail=str(error)) from error
    except FoodReferenceUnavailableError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="FoodData-Central-Referenzdaten nicht erreichbar",
        ) from error
    except SQLAlchemyError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Importdatenbank nicht verfügbar",
        ) from error
    return FoodReferenceImportResponse(
        dataset=result.dataset.value,
        parsed=result.parsed,
        created=result.created,
        updated=result.updated,
        unchanged=result.unchanged,
        complete=result.complete,
    )


@router.get("/stats", response_model=FoodReferenceStatsResponse)
def read_food_reference_stats(session: DatabaseSession) -> FoodReferenceStatsResponse:
    complete_filter = (
        FoodReferenceItem.calories_per_100.is_not(None),
        FoodReferenceItem.protein_per_100.is_not(None),
        FoodReferenceItem.carbs_per_100.is_not(None),
        FoodReferenceItem.fat_per_100.is_not(None),
    )
    by_data_type = {
        data_type: count
        for data_type, count in session.execute(
            select(FoodReferenceItem.data_type, func.count())
            .group_by(FoodReferenceItem.data_type)
            .order_by(FoodReferenceItem.data_type)
        )
    }
    return FoodReferenceStatsResponse(
        total=session.scalar(select(func.count()).select_from(FoodReferenceItem)) or 0,
        complete=(
            session.scalar(
                select(func.count())
                .select_from(FoodReferenceItem)
                .where(*complete_filter)
            )
            or 0
        ),
        by_data_type=by_data_type,
    )


@router.get("/search", response_model=list[FoodReferenceSearchResult])
def search_food_references(
    session: DatabaseSession,
    query: Annotated[str, Query(min_length=1, max_length=300)],
    limit: Annotated[int, Query(ge=1, le=25)] = 5,
) -> list[FoodReferenceSearchResult]:
    items = tuple(session.scalars(select(FoodReferenceItem)))
    by_external_id = {item.external_id: item for item in items}
    suggestion = suggest_food(
        query,
        tuple(
            FoodSearchCandidate(
                external_id=item.external_id,
                name=item.description,
                data_type=item.data_type,
            )
            for item in items
        ),
        result_limit=limit,
    )
    return [
        FoodReferenceSearchResult(
            fdc_id=candidate.external_id,
            description=candidate.name,
            data_type=candidate.data_type,
            score=candidate.score,
            calories_per_100=by_external_id[candidate.external_id].calories_per_100,
            protein_per_100=by_external_id[candidate.external_id].protein_per_100,
            carbs_per_100=by_external_id[candidate.external_id].carbs_per_100,
            fat_per_100=by_external_id[candidate.external_id].fat_per_100,
        )
        for candidate in suggestion.candidates
    ]
