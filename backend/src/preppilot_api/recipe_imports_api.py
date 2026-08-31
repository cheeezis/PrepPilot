from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from preppilot_api.database import get_session
from preppilot_api.models import Food, RecipeImport, RecipeImportStatus
from preppilot_api.recipe_catalog_promotion import (
    PromoteRecipeImportCommand,
    RecipePromotionError,
    promote_recipe_import,
)
from preppilot_api.recipe_import_quality import (
    assess_recipe_import,
    assessment_sort_key,
)
from preppilot_api.recipe_imports import (
    CreateRecipeImportCommand,
    RecipeImportDecisionError,
    RecipeImportNotFoundError,
    ReviewDecisionCommand,
    apply_review_decision,
    create_recipe_import,
    get_recipe_import,
    ingredients_for_import,
    list_recipe_imports,
    process_recipe_import,
)
from preppilot_api.recipe_sources import (
    RecipeSourceNotFoundError,
    RecipeSourcePayloadError,
    RecipeSourceUnavailableError,
    TheMealDbSource,
    get_themealdb_source,
)

router = APIRouter(prefix="/api/internal/recipe-imports", tags=["recipe-imports"])
DatabaseSession = Annotated[Session, Depends(get_session)]
TheMealDbDependency = Annotated[TheMealDbSource, Depends(get_themealdb_source)]


class ImportedIngredientResponse(BaseModel):
    id: int
    position: int
    raw_line: str
    raw_name: str
    raw_amount: str | None
    raw_unit: str | None
    status: str
    review_reason: str | None
    food_key: str | None
    normalized_amount: float | None
    normalized_unit: str | None


class RecipeImportResponse(BaseModel):
    id: int
    source_name: str
    external_id: str
    fetched_at: str
    content_hash: str
    status: str
    quality_score: int
    review_priority: str
    quality_issues: list[str]
    unknown_ingredient_count: int
    review_item_count: int
    raw_payload: dict[str, object]
    ingredients: list[ImportedIngredientResponse]


class CreatedRecipeImportResponse(BaseModel):
    created: bool
    recipe_import: RecipeImportResponse


class PromotedMealResponse(BaseModel):
    created: bool
    meal_id: int
    catalog_key: str
    source_recipe_import_id: int


class BatchRecipeImportResult(BaseModel):
    external_id: str
    name: str
    created: bool
    error: str | None = None
    recipe_import: RecipeImportResponse | None = None


class BatchRecipeImportResponse(BaseModel):
    category: str
    discovered: int
    imported: int
    created: int
    failed: int
    results: list[BatchRecipeImportResult]


class ReprocessedRecipeImportsResponse(BaseModel):
    reprocessed: int
    recipe_imports: list[RecipeImportResponse]


@router.post("", response_model=CreatedRecipeImportResponse)
def receive_recipe_import(
    command: CreateRecipeImportCommand,
    response: Response,
    session: DatabaseSession,
) -> CreatedRecipeImportResponse:
    try:
        recipe_import, created = create_recipe_import(session, command)
        session.commit()
    except SQLAlchemyError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Importdatenbank nicht verfügbar",
        ) from error
    response.status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    return CreatedRecipeImportResponse(
        created=created,
        recipe_import=_serialize_recipe_import(session, recipe_import),
    )


@router.get("", response_model=list[RecipeImportResponse])
def read_recipe_imports(
    session: DatabaseSession,
    import_status: RecipeImportStatus | None = None,
) -> list[RecipeImportResponse]:
    recipe_imports = list(list_recipe_imports(session, import_status))
    recipe_imports.sort(
        key=lambda item: (
            *assessment_sort_key(assess_recipe_import(session, item)),
            item.id,
        )
    )
    return [_serialize_recipe_import(session, item) for item in recipe_imports]


@router.post(
    "/sources/themealdb/{external_id}",
    response_model=CreatedRecipeImportResponse,
)
def import_themealdb_recipe(
    external_id: str,
    response: Response,
    session: DatabaseSession,
    source: TheMealDbDependency,
) -> CreatedRecipeImportResponse:
    try:
        fetched = source.fetch(external_id)
        recipe_import, created = create_recipe_import(
            session,
            fetched.command,
            source_payload=fetched.source_payload,
        )
        session.commit()
    except RecipeSourceNotFoundError as error:
        session.rollback()
        raise HTTPException(
            status_code=404, detail="TheMealDB-Rezept nicht gefunden"
        ) from error
    except RecipeSourcePayloadError as error:
        session.rollback()
        raise HTTPException(status_code=422, detail=str(error)) from error
    except RecipeSourceUnavailableError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="TheMealDB nicht erreichbar",
        ) from error
    except SQLAlchemyError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Importdatenbank nicht verfügbar",
        ) from error
    response.status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    return CreatedRecipeImportResponse(
        created=created,
        recipe_import=_serialize_recipe_import(session, recipe_import),
    )


@router.post(
    "/sources/themealdb/batches/categories/{category}",
    response_model=BatchRecipeImportResponse,
)
def import_themealdb_category(
    category: str,
    session: DatabaseSession,
    source: TheMealDbDependency,
    limit: int = 10,
) -> BatchRecipeImportResponse:
    try:
        references = source.discover_category(category, limit=limit)
        results: list[BatchRecipeImportResult] = []
        for reference in references:
            try:
                fetched = source.fetch(reference.external_id)
                recipe_import, created = create_recipe_import(
                    session,
                    fetched.command,
                    source_payload=fetched.source_payload,
                )
                results.append(
                    BatchRecipeImportResult(
                        external_id=reference.external_id,
                        name=reference.name,
                        created=created,
                        recipe_import=_serialize_recipe_import(
                            session, recipe_import
                        ),
                    )
                )
            except RecipeSourceNotFoundError:
                results.append(
                    BatchRecipeImportResult(
                        external_id=reference.external_id,
                        name=reference.name,
                        created=False,
                        error="not_found",
                    )
                )
            except RecipeSourcePayloadError:
                results.append(
                    BatchRecipeImportResult(
                        external_id=reference.external_id,
                        name=reference.name,
                        created=False,
                        error="invalid_payload",
                    )
                )
            except RecipeSourceUnavailableError:
                results.append(
                    BatchRecipeImportResult(
                        external_id=reference.external_id,
                        name=reference.name,
                        created=False,
                        error="source_unavailable",
                    )
                )
        session.commit()
    except RecipeSourcePayloadError as error:
        session.rollback()
        raise HTTPException(status_code=422, detail=str(error)) from error
    except RecipeSourceUnavailableError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="TheMealDB nicht erreichbar",
        ) from error
    except SQLAlchemyError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Importdatenbank nicht verfügbar",
        ) from error

    imported = sum(result.recipe_import is not None for result in results)
    created_count = sum(result.created for result in results)
    return BatchRecipeImportResponse(
        category=category.strip(),
        discovered=len(references),
        imported=imported,
        created=created_count,
        failed=len(results) - imported,
        results=results,
    )


@router.post("/reprocess", response_model=ReprocessedRecipeImportsResponse)
def reprocess_open_recipe_imports(
    session: DatabaseSession,
) -> ReprocessedRecipeImportsResponse:
    try:
        recipe_imports = [
            item
            for item in list_recipe_imports(session)
            if item.status != RecipeImportStatus.REJECTED
        ]
        for recipe_import in recipe_imports:
            recipe_import.status = RecipeImportStatus.RECEIVED
            process_recipe_import(session, recipe_import.id)
        session.commit()
    except SQLAlchemyError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Importdatenbank nicht verfügbar",
        ) from error

    recipe_imports.sort(
        key=lambda item: (
            *assessment_sort_key(assess_recipe_import(session, item)),
            item.id,
        )
    )
    return ReprocessedRecipeImportsResponse(
        reprocessed=len(recipe_imports),
        recipe_imports=[
            _serialize_recipe_import(session, item) for item in recipe_imports
        ],
    )


@router.get("/{recipe_import_id}", response_model=RecipeImportResponse)
def read_recipe_import(
    recipe_import_id: int, session: DatabaseSession
) -> RecipeImportResponse:
    try:
        recipe_import = get_recipe_import(session, recipe_import_id)
    except RecipeImportNotFoundError as error:
        raise HTTPException(
            status_code=404, detail="Rezeptimport nicht gefunden"
        ) from error
    return _serialize_recipe_import(session, recipe_import)


@router.post("/{recipe_import_id}/decisions", response_model=RecipeImportResponse)
def decide_recipe_import(
    recipe_import_id: int,
    command: ReviewDecisionCommand,
    session: DatabaseSession,
) -> RecipeImportResponse:
    try:
        recipe_import = apply_review_decision(session, recipe_import_id, command)
        session.commit()
    except RecipeImportNotFoundError as error:
        session.rollback()
        raise HTTPException(
            status_code=404, detail="Rezeptimport nicht gefunden"
        ) from error
    except RecipeImportDecisionError as error:
        session.rollback()
        raise HTTPException(status_code=422, detail=str(error)) from error
    return _serialize_recipe_import(session, recipe_import)


@router.post("/{recipe_import_id}/reprocess", response_model=RecipeImportResponse)
def reprocess_recipe_import(
    recipe_import_id: int, session: DatabaseSession
) -> RecipeImportResponse:
    try:
        recipe_import = get_recipe_import(session, recipe_import_id)
        if recipe_import.status == RecipeImportStatus.REJECTED:
            raise RecipeImportDecisionError(
                "rejected recipe imports cannot be reprocessed"
            )
        recipe_import.status = RecipeImportStatus.RECEIVED
        process_recipe_import(session, recipe_import_id)
        session.commit()
    except RecipeImportNotFoundError as error:
        session.rollback()
        raise HTTPException(
            status_code=404, detail="Rezeptimport nicht gefunden"
        ) from error
    except RecipeImportDecisionError as error:
        session.rollback()
        raise HTTPException(status_code=422, detail=str(error)) from error
    return _serialize_recipe_import(session, recipe_import)


@router.post("/{recipe_import_id}/promote", response_model=PromotedMealResponse)
def promote_reviewed_recipe_import(
    recipe_import_id: int,
    command: PromoteRecipeImportCommand,
    session: DatabaseSession,
) -> PromotedMealResponse:
    try:
        meal, created = promote_recipe_import(session, recipe_import_id, command)
        session.commit()
    except RecipeImportNotFoundError as error:
        session.rollback()
        raise HTTPException(
            status_code=404, detail="Rezeptimport nicht gefunden"
        ) from error
    except RecipePromotionError as error:
        session.rollback()
        raise HTTPException(status_code=422, detail=str(error)) from error
    except SQLAlchemyError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Mahlzeitenkatalog nicht verfügbar",
        ) from error
    return PromotedMealResponse(
        created=created,
        meal_id=meal.id,
        catalog_key=meal.catalog_key,
        source_recipe_import_id=recipe_import_id,
    )


def _serialize_recipe_import(
    session: Session, recipe_import: RecipeImport
) -> RecipeImportResponse:
    ingredients = ingredients_for_import(session, recipe_import.id)
    assessment = assess_recipe_import(session, recipe_import)
    food_ids = {ingredient.food_id for ingredient in ingredients if ingredient.food_id}
    foods = {
        food.id: food
        for food in session.scalars(select(Food).where(Food.id.in_(food_ids)))
    }
    return RecipeImportResponse(
        id=recipe_import.id,
        source_name=recipe_import.source_name,
        external_id=recipe_import.external_id,
        fetched_at=recipe_import.fetched_at.isoformat(),
        content_hash=recipe_import.content_hash,
        status=recipe_import.status.value,
        quality_score=assessment.score,
        review_priority=assessment.priority.value,
        quality_issues=list(assessment.issues),
        unknown_ingredient_count=assessment.unknown_ingredient_count,
        review_item_count=assessment.review_item_count,
        raw_payload=recipe_import.raw_payload,
        ingredients=[
            ImportedIngredientResponse(
                id=ingredient.id,
                position=ingredient.position,
                raw_line=ingredient.raw_line,
                raw_name=ingredient.raw_name,
                raw_amount=ingredient.raw_amount,
                raw_unit=ingredient.raw_unit,
                status=ingredient.status.value,
                review_reason=(
                    None
                    if ingredient.review_reason is None
                    else ingredient.review_reason.value
                ),
                food_key=(
                    None
                    if ingredient.food_id is None
                    else foods[ingredient.food_id].catalog_key
                ),
                normalized_amount=(
                    None
                    if ingredient.normalized_amount is None
                    else float(ingredient.normalized_amount)
                ),
                normalized_unit=(
                    None
                    if ingredient.food_id is None
                    else foods[ingredient.food_id].unit.value
                ),
            )
            for ingredient in ingredients
        ],
    )
