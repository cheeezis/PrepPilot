from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from preppilot_api.database import get_session
from preppilot_api.food_concepts import (
    FoodConceptNotFoundError,
    FoodSourceIdentifierConflictError,
    FoodSourceIdentifierNotFoundError,
)
from preppilot_api.models import (
    Food,
    FoodConcept,
    FoodSourceIdentifier,
    RecipeImport,
    RecipeImportIngredient,
)
from preppilot_api.recipe_imports import resolve_recipe_ingredient_identity


class ImportReviewSummary(BaseModel):
    recipe_count: int
    open_identity_count: int
    review_ingredient_count: int


class FoodConceptOption(BaseModel):
    key: str
    name: str
    profile_count: int


class OpenFoodIdentity(BaseModel):
    id: int
    source_name: str
    external_id: str
    source_label: str | None
    source_url: str | None
    ingredient_count: int
    recipe_count: int


class RecipeIngredientReview(BaseModel):
    id: int
    raw_line: str
    status: str
    review_reason: str | None
    source_identifier_id: int | None
    source_label: str | None
    concept_key: str | None
    food_key: str | None


class RecipeImportReview(BaseModel):
    id: int
    title: str
    source_name: str
    external_id: str
    status: str
    ingredients: list[RecipeIngredientReview]


class ImportReviewOverview(BaseModel):
    summary: ImportReviewSummary
    open_identities: list[OpenFoodIdentity]
    concepts: list[FoodConceptOption]
    recipes: list[RecipeImportReview]


class ResolveFoodIdentityRequest(BaseModel):
    concept_key: str = Field(min_length=1, max_length=100)


router = APIRouter(prefix="/api/internal/import-review", tags=["internal-import-review"])
DatabaseSession = Annotated[Session, Depends(get_session)]


@router.get("", response_model=ImportReviewOverview)
def get_import_review_overview(session: DatabaseSession) -> ImportReviewOverview:
    return _build_overview(session)


@router.post(
    "/food-identities/{identifier_id}/resolve",
    response_model=ImportReviewOverview,
)
def resolve_food_identity(
    identifier_id: int,
    request: ResolveFoodIdentityRequest,
    session: DatabaseSession,
) -> ImportReviewOverview:
    try:
        resolve_recipe_ingredient_identity(
            session,
            identifier_id=identifier_id,
            concept_key=request.concept_key,
        )
        session.commit()
    except (FoodConceptNotFoundError, FoodSourceIdentifierNotFoundError) as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except FoodSourceIdentifierConflictError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error
    return _build_overview(session)


def _build_overview(session: Session) -> ImportReviewOverview:
    foods = tuple(session.scalars(select(Food).order_by(Food.id)))
    concepts = tuple(session.scalars(select(FoodConcept).order_by(FoodConcept.name)))
    identifiers = tuple(
        session.scalars(select(FoodSourceIdentifier).order_by(FoodSourceIdentifier.id))
    )
    recipe_imports = tuple(
        session.scalars(select(RecipeImport).order_by(RecipeImport.id.desc()).limit(100))
    )
    ingredients = tuple(
        session.scalars(
            select(RecipeImportIngredient).order_by(
                RecipeImportIngredient.recipe_import_id,
                RecipeImportIngredient.position,
            )
        )
    )

    foods_by_id = {food.id: food for food in foods}
    concepts_by_id = {concept.id: concept for concept in concepts}
    identifiers_by_id = {identifier.id: identifier for identifier in identifiers}
    profile_counts: dict[int, int] = {}
    for food in foods:
        profile_counts[food.concept_id] = profile_counts.get(food.concept_id, 0) + 1

    ingredients_by_recipe: dict[int, list[RecipeImportIngredient]] = {}
    ingredients_by_identifier: dict[int, list[RecipeImportIngredient]] = {}
    for ingredient in ingredients:
        ingredients_by_recipe.setdefault(ingredient.recipe_import_id, []).append(
            ingredient
        )
        if ingredient.source_identifier_id is not None:
            ingredients_by_identifier.setdefault(
                ingredient.source_identifier_id, []
            ).append(ingredient)

    open_identities = []
    for identifier in identifiers:
        if identifier.concept_id is not None:
            continue
        linked_ingredients = ingredients_by_identifier.get(identifier.id, [])
        open_identities.append(
            OpenFoodIdentity(
                id=identifier.id,
                source_name=identifier.source_name,
                external_id=identifier.external_id,
                source_label=identifier.source_label,
                source_url=identifier.source_url,
                ingredient_count=len(linked_ingredients),
                recipe_count=len(
                    {ingredient.recipe_import_id for ingredient in linked_ingredients}
                ),
            )
        )

    return ImportReviewOverview(
        summary=ImportReviewSummary(
            recipe_count=session.scalar(
                select(func.count()).select_from(RecipeImport)
            )
            or 0,
            open_identity_count=len(open_identities),
            review_ingredient_count=sum(
                ingredient.status.value == "needs_review" for ingredient in ingredients
            ),
        ),
        open_identities=open_identities,
        concepts=[
            FoodConceptOption(
                key=concept.key,
                name=concept.name,
                profile_count=profile_counts.get(concept.id, 0),
            )
            for concept in concepts
        ],
        recipes=[
            RecipeImportReview(
                id=recipe_import.id,
                title=_recipe_title(recipe_import),
                source_name=recipe_import.source_name,
                external_id=recipe_import.external_id,
                status=recipe_import.status.value,
                ingredients=[
                    _serialize_ingredient(
                        ingredient,
                        foods_by_id=foods_by_id,
                        concepts_by_id=concepts_by_id,
                        identifiers_by_id=identifiers_by_id,
                    )
                    for ingredient in ingredients_by_recipe.get(recipe_import.id, [])
                ],
            )
            for recipe_import in recipe_imports
        ],
    )


def _serialize_ingredient(
    ingredient: RecipeImportIngredient,
    *,
    foods_by_id: dict[int, Food],
    concepts_by_id: dict[int, FoodConcept],
    identifiers_by_id: dict[int, FoodSourceIdentifier],
) -> RecipeIngredientReview:
    food = foods_by_id.get(ingredient.food_id) if ingredient.food_id is not None else None
    concept = (
        concepts_by_id.get(ingredient.concept_id)
        if ingredient.concept_id is not None
        else None
    )
    identifier = (
        identifiers_by_id.get(ingredient.source_identifier_id)
        if ingredient.source_identifier_id is not None
        else None
    )
    return RecipeIngredientReview(
        id=ingredient.id,
        raw_line=ingredient.raw_line,
        status=ingredient.status.value,
        review_reason=(
            ingredient.review_reason.value
            if ingredient.review_reason is not None
            else None
        ),
        source_identifier_id=ingredient.source_identifier_id,
        source_label=identifier.source_label if identifier is not None else None,
        concept_key=concept.key if concept is not None else None,
        food_key=food.catalog_key if food is not None else None,
    )


def _recipe_title(recipe_import: RecipeImport) -> str:
    title = recipe_import.raw_payload.get("title")
    return title if isinstance(title, str) and title.strip() else recipe_import.external_id
