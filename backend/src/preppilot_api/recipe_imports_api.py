from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from preppilot_api.database import get_session
from preppilot_api.models import Food, RecipeImport, RecipeImportStatus
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

router = APIRouter(prefix="/api/internal/recipe-imports", tags=["recipe-imports"])
DatabaseSession = Annotated[Session, Depends(get_session)]


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
    raw_payload: dict[str, object]
    ingredients: list[ImportedIngredientResponse]


class CreatedRecipeImportResponse(BaseModel):
    created: bool
    recipe_import: RecipeImportResponse


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
    return [
        _serialize_recipe_import(session, recipe_import)
        for recipe_import in list_recipe_imports(session, import_status)
    ]


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


def _serialize_recipe_import(
    session: Session, recipe_import: RecipeImport
) -> RecipeImportResponse:
    ingredients = ingredients_for_import(session, recipe_import.id)
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
