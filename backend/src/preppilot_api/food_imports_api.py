from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from preppilot_api.database import get_session
from preppilot_api.food_auto_resolution import auto_resolve_recipe_foods
from preppilot_api.food_imports import (
    FoodImportNotFoundError,
    FoodImportPromotionError,
    PromoteFoodImportCommand,
    create_food_import,
    find_latest_food_import,
    get_food_import,
    list_food_imports,
    promote_food_import,
)
from preppilot_api.food_reference import reference_to_food_import
from preppilot_api.food_sources import (
    FoodDataCentralSource,
    FoodSearchCandidate,
    FoodSourceNotFoundError,
    FoodSourcePayloadError,
    FoodSourceUnavailableError,
    get_fooddata_central_source,
)
from preppilot_api.food_suggestions import (
    LocalFoodCandidate,
    suggest_food,
    suggest_local_food,
)
from preppilot_api.models import (
    Food,
    FoodImport,
    FoodReferenceItem,
    ImportedIngredientStatus,
    ImportReviewReason,
    RecipeImport,
    RecipeImportIngredient,
    RecipeImportStatus,
    ReviewDecisionAction,
)
from preppilot_api.recipe_imports import (
    RecipeImportDecisionError,
    ReviewDecisionCommand,
    apply_review_decision,
    normalize_text,
    process_recipe_import,
)

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


class FoodSuggestionCandidateResponse(BaseModel):
    fdc_id: str
    name: str
    data_type: str
    score: int


class FoodSuggestionResponse(BaseModel):
    ingredient_name: str
    normalized_name: str
    occurrence_count: int
    status: str
    local_food_key: str | None
    selected_fdc_id: str | None
    food_import_id: int | None
    food_import_created: bool
    candidates: list[FoodSuggestionCandidateResponse]


class FoodSuggestionBatchResponse(BaseModel):
    unique_unknown_ingredients: int
    processed: int
    local_aliases_added: int
    selected: int
    imported: int
    created: int
    ambiguous: int
    no_match: int
    failed: int
    suggestions: list[FoodSuggestionResponse]


class FoodAutoResolutionItemResponse(BaseModel):
    ingredient_name: str
    normalized_name: str
    occurrence_count: int
    status: str
    fdc_id: str | None
    reference_name: str | None
    score: int | None
    catalog_key: str | None
    food_id: int | None


class FoodAutoResolutionResponse(BaseModel):
    dry_run: bool
    unique_unknown_ingredients: int
    processed: int
    eligible: int
    promoted: int
    aliases_added: int
    reused_foods: int
    ambiguous: int
    no_match: int
    incomplete: int
    conflicts: int
    ready_recipes_before: int
    ready_recipes_after: int
    items: list[FoodAutoResolutionItemResponse]


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


@router.post(
    "/suggestions/from-recipe-inbox",
    response_model=FoodSuggestionBatchResponse,
)
def suggest_foods_for_recipe_inbox(
    session: DatabaseSession,
    source: FoodDataCentralDependency,
    limit: Annotated[int, Query(ge=1, le=25)] = 10,
) -> FoodSuggestionBatchResponse:
    ingredients = tuple(
        session.scalars(
            select(RecipeImportIngredient)
            .where(
                RecipeImportIngredient.status
                == ImportedIngredientStatus.NEEDS_REVIEW,
                RecipeImportIngredient.review_reason
                == ImportReviewReason.UNKNOWN_FOOD,
            )
            .order_by(RecipeImportIngredient.id)
        )
    )
    grouped: dict[str, tuple[str, int, RecipeImportIngredient]] = {}
    for ingredient in ingredients:
        normalized_name = normalize_text(ingredient.raw_name)
        display_name, count, representative = grouped.get(
            normalized_name, (ingredient.raw_name.strip(), 0, ingredient)
        )
        grouped[normalized_name] = (display_name, count + 1, representative)
    ordered = sorted(
        grouped.items(),
        key=lambda item: (-item[1][1], item[0]),
    )
    local_candidates = tuple(
        LocalFoodCandidate(
            food_id=food.id,
            catalog_key=food.catalog_key,
            name=food.name,
        )
        for food in session.scalars(select(Food).order_by(Food.id))
    )
    reference_items = tuple(session.scalars(select(FoodReferenceItem)))
    reference_by_external_id = {
        item.external_id: item for item in reference_items
    }
    reference_candidates = tuple(
        FoodSearchCandidate(
            external_id=item.external_id,
            name=item.description,
            data_type=item.data_type,
        )
        for item in reference_items
    )

    suggestions: list[FoodSuggestionResponse] = []
    try:
        for _, (ingredient_name, occurrence_count, representative) in ordered[:limit]:
            try:
                local_suggestion = suggest_local_food(
                    ingredient_name, local_candidates
                )
                if local_suggestion is not None:
                    apply_review_decision(
                        session,
                        representative.recipe_import_id,
                        ReviewDecisionCommand(
                            action=ReviewDecisionAction.ADD_ALIAS,
                            ingredient_id=representative.id,
                            food_key=local_suggestion.catalog_key,
                            alias=ingredient_name,
                        ),
                    )
                    suggestions.append(
                        FoodSuggestionResponse(
                            ingredient_name=ingredient_name,
                            normalized_name=normalize_text(ingredient_name),
                            occurrence_count=occurrence_count,
                            status="local_alias_added",
                            local_food_key=local_suggestion.catalog_key,
                            selected_fdc_id=None,
                            food_import_id=None,
                            food_import_created=False,
                            candidates=[],
                        )
                    )
                    continue
                suggestion = suggest_food(
                    ingredient_name,
                    (
                        reference_candidates
                        if reference_candidates
                        else source.search(ingredient_name, limit=5)
                    ),
                    result_limit=5,
                )
                food_import_id: int | None = None
                food_import_created = False
                item_status = suggestion.status.value
                if suggestion.selected_external_id is not None:
                    reference_item = reference_by_external_id.get(
                        suggestion.selected_external_id
                    )
                    command = (
                        reference_to_food_import(reference_item)
                        if reference_item is not None
                        else source.fetch(suggestion.selected_external_id)
                    )
                    existing_import = (
                        find_latest_food_import(
                            session,
                            reference_item.source_name,
                            reference_item.external_id,
                        )
                        if reference_item is not None
                        else None
                    )
                    if existing_import is not None:
                        food_import = existing_import
                        food_import_created = False
                    else:
                        food_import, food_import_created = create_food_import(
                            session, command
                        )
                    food_import_id = food_import.id
                suggestions.append(
                    FoodSuggestionResponse(
                        ingredient_name=ingredient_name,
                        normalized_name=suggestion.normalized_name,
                        occurrence_count=occurrence_count,
                        status=item_status,
                        local_food_key=None,
                        selected_fdc_id=suggestion.selected_external_id,
                        food_import_id=food_import_id,
                        food_import_created=food_import_created,
                        candidates=[
                            FoodSuggestionCandidateResponse(
                                fdc_id=candidate.external_id,
                                name=candidate.name,
                                data_type=candidate.data_type,
                                score=candidate.score,
                            )
                            for candidate in suggestion.candidates
                        ],
                    )
                )
            except FoodSourceNotFoundError:
                suggestions.append(
                    _failed_suggestion(
                        ingredient_name, occurrence_count, "not_found"
                    )
                )
            except FoodSourcePayloadError:
                suggestions.append(
                    _failed_suggestion(
                        ingredient_name, occurrence_count, "invalid_payload"
                    )
                )
            except FoodSourceUnavailableError:
                suggestions.append(
                    _failed_suggestion(
                        ingredient_name, occurrence_count, "source_unavailable"
                    )
                )
        local_aliases_added = sum(
            item.status == "local_alias_added" for item in suggestions
        )
        if local_aliases_added:
            recipe_imports = tuple(
                session.scalars(
                    select(RecipeImport).where(
                        RecipeImport.status != RecipeImportStatus.REJECTED
                    )
                )
            )
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

    selected = sum(item.selected_fdc_id is not None for item in suggestions)
    imported = sum(item.food_import_id is not None for item in suggestions)
    created = sum(item.food_import_created for item in suggestions)
    ambiguous = sum(item.status == "ambiguous" for item in suggestions)
    no_match = sum(item.status == "no_match" for item in suggestions)
    failed = sum(
        item.status in {"not_found", "invalid_payload", "source_unavailable"}
        for item in suggestions
    )
    return FoodSuggestionBatchResponse(
        unique_unknown_ingredients=len(grouped),
        processed=len(suggestions),
        local_aliases_added=local_aliases_added,
        selected=selected,
        imported=imported,
        created=created,
        ambiguous=ambiguous,
        no_match=no_match,
        failed=failed,
        suggestions=suggestions,
    )


@router.post(
    "/auto-resolve/from-recipe-inbox",
    response_model=FoodAutoResolutionResponse,
)
def auto_resolve_foods_for_recipe_inbox(
    session: DatabaseSession,
    limit: Annotated[int, Query(ge=1, le=250)] = 250,
    dry_run: bool = True,
) -> FoodAutoResolutionResponse:
    try:
        result = auto_resolve_recipe_foods(
            session, limit=limit, dry_run=dry_run
        )
        if dry_run:
            session.rollback()
        else:
            session.commit()
    except (FoodImportPromotionError, RecipeImportDecisionError) as error:
        session.rollback()
        raise HTTPException(status_code=422, detail=str(error)) from error
    except SQLAlchemyError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Lebensmittelkatalog nicht verfügbar",
        ) from error
    return FoodAutoResolutionResponse(
        dry_run=result.dry_run,
        unique_unknown_ingredients=result.unique_unknown_ingredients,
        processed=result.processed,
        eligible=result.eligible,
        promoted=result.promoted,
        aliases_added=result.aliases_added,
        reused_foods=result.reused_foods,
        ambiguous=result.ambiguous,
        no_match=result.no_match,
        incomplete=result.incomplete,
        conflicts=result.conflicts,
        ready_recipes_before=result.ready_recipes_before,
        ready_recipes_after=result.ready_recipes_after,
        items=[
            FoodAutoResolutionItemResponse(
                ingredient_name=item.ingredient_name,
                normalized_name=item.normalized_name,
                occurrence_count=item.occurrence_count,
                status=item.status,
                fdc_id=item.fdc_id,
                reference_name=item.reference_name,
                score=item.score,
                catalog_key=item.catalog_key,
                food_id=item.food_id,
            )
            for item in result.items
        ],
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


def _failed_suggestion(
    ingredient_name: str, occurrence_count: int, status_value: str
) -> FoodSuggestionResponse:
    return FoodSuggestionResponse(
        ingredient_name=ingredient_name,
        normalized_name=normalize_text(ingredient_name),
        occurrence_count=occurrence_count,
        status=status_value,
        local_food_key=None,
        selected_fdc_id=None,
        food_import_id=None,
        food_import_created=False,
        candidates=[],
    )
