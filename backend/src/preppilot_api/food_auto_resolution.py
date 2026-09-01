import re
import unicodedata
from dataclasses import dataclass, replace

from sqlalchemy import select
from sqlalchemy.orm import Session

from preppilot_api.food_imports import (
    PromoteFoodImportCommand,
    create_food_import,
    find_latest_food_import,
    promote_food_import,
)
from preppilot_api.food_reference import reference_to_food_import
from preppilot_api.food_sources import FoodSearchCandidate
from preppilot_api.food_suggestions import FoodSuggestionStatus, suggest_food
from preppilot_api.models import (
    Food,
    FoodAlias,
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
    ReviewDecisionCommand,
    apply_review_decision,
    normalize_text,
    process_recipe_import,
)


@dataclass(frozen=True)
class AutoResolutionItem:
    ingredient_name: str
    normalized_name: str
    occurrence_count: int
    status: str
    fdc_id: str | None = None
    reference_name: str | None = None
    score: int | None = None
    catalog_key: str | None = None
    food_id: int | None = None


@dataclass(frozen=True)
class AutoResolutionResult:
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
    items: tuple[AutoResolutionItem, ...]


@dataclass(frozen=True)
class _PlannedResolution:
    response: AutoResolutionItem
    representative: RecipeImportIngredient | None = None
    reference: FoodReferenceItem | None = None
    existing_food_id: int | None = None


def auto_resolve_recipe_foods(
    session: Session, *, limit: int, dry_run: bool
) -> AutoResolutionResult:
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
        normalized = normalize_text(ingredient.raw_name)
        display, count, representative = grouped.get(
            normalized, (ingredient.raw_name.strip(), 0, ingredient)
        )
        grouped[normalized] = (display, count + 1, representative)
    ordered = sorted(grouped.items(), key=lambda item: (-item[1][1], item[0]))

    references = tuple(session.scalars(select(FoodReferenceItem)))
    references_by_id = {item.external_id: item for item in references}
    candidates = tuple(
        FoodSearchCandidate(item.external_id, item.description, item.data_type)
        for item in references
    )
    foods = tuple(session.scalars(select(Food).order_by(Food.id)))
    food_by_key = {food.catalog_key: food for food in foods}
    food_by_external_id = {
        external_id: food
        for food, external_id in session.execute(
            select(Food, FoodImport.external_id).join(
                FoodImport, Food.source_food_import_id == FoodImport.id
            )
        )
    }
    aliases = {
        alias.normalized_alias: alias
        for alias in session.scalars(select(FoodAlias))
    }
    planned_external_keys: dict[str, str] = {}
    planned_keys: dict[str, str] = {}
    plans: list[_PlannedResolution] = []

    for normalized, (ingredient_name, occurrence_count, representative) in ordered[
        :limit
    ]:
        suggestion = suggest_food(ingredient_name, candidates, result_limit=5)
        if suggestion.status == FoodSuggestionStatus.NO_MATCH:
            plans.append(
                _PlannedResolution(
                    AutoResolutionItem(
                        ingredient_name=ingredient_name,
                        normalized_name=normalized,
                        occurrence_count=occurrence_count,
                        status="no_match",
                    )
                )
            )
            continue
        if suggestion.selected_external_id is None:
            plans.append(
                _PlannedResolution(
                    AutoResolutionItem(
                        ingredient_name=ingredient_name,
                        normalized_name=normalized,
                        occurrence_count=occurrence_count,
                        status="ambiguous",
                    )
                )
            )
            continue
        reference = references_by_id[suggestion.selected_external_id]
        top = suggestion.candidates[0]
        if not _is_complete(reference):
            plans.append(
                _PlannedResolution(
                    AutoResolutionItem(
                        ingredient_name=ingredient_name,
                        normalized_name=normalized,
                        occurrence_count=occurrence_count,
                        status="incomplete_reference",
                        fdc_id=reference.external_id,
                        reference_name=reference.description,
                        score=top.score,
                    )
                )
            )
            continue

        existing_food = food_by_external_id.get(reference.external_id)
        catalog_key = (
            existing_food.catalog_key
            if existing_food is not None
            else planned_external_keys.get(reference.external_id)
            or canonical_catalog_key(ingredient_name, reference.external_id)
        )
        key_food = food_by_key.get(catalog_key)
        planned_external_id = planned_keys.get(catalog_key)
        alias = aliases.get(normalized)
        conflict = (
            (key_food is not None and key_food.id != getattr(existing_food, "id", None))
            or (
                planned_external_id is not None
                and planned_external_id != reference.external_id
            )
            or (
                alias is not None
                and (existing_food is None or alias.food_id != existing_food.id)
            )
        )
        if conflict:
            plans.append(
                _PlannedResolution(
                    AutoResolutionItem(
                        ingredient_name=ingredient_name,
                        normalized_name=normalized,
                        occurrence_count=occurrence_count,
                        status="conflict",
                        fdc_id=reference.external_id,
                        reference_name=reference.description,
                        score=top.score,
                        catalog_key=catalog_key,
                    )
                )
            )
            continue
        planned_external_keys[reference.external_id] = catalog_key
        planned_keys[catalog_key] = reference.external_id
        plans.append(
            _PlannedResolution(
                AutoResolutionItem(
                    ingredient_name=ingredient_name,
                    normalized_name=normalized,
                    occurrence_count=occurrence_count,
                    status="eligible",
                    fdc_id=reference.external_id,
                    reference_name=reference.description,
                    score=top.score,
                    catalog_key=catalog_key,
                    food_id=None if existing_food is None else existing_food.id,
                ),
                representative=representative,
                reference=reference,
                existing_food_id=None if existing_food is None else existing_food.id,
            )
        )

    ready_before = _ready_recipe_count(session)
    promoted = 0
    aliases_added = 0
    reused_foods = (
        sum(
            plan.response.status == "eligible"
            and plan.existing_food_id is not None
            for plan in plans
        )
        if dry_run
        else 0
    )
    resolved_items: list[AutoResolutionItem] = []
    created_foods: dict[str, Food] = {}
    if not dry_run:
        for plan in plans:
            if plan.response.status != "eligible":
                resolved_items.append(plan.response)
                continue
            assert plan.reference is not None
            assert plan.representative is not None
            food = (
                session.get(Food, plan.existing_food_id)
                if plan.existing_food_id is not None
                else created_foods.get(plan.reference.external_id)
            )
            if food is None:
                food_import = find_latest_food_import(
                    session, plan.reference.source_name, plan.reference.external_id
                )
                if food_import is None:
                    food_import, _ = create_food_import(
                        session, reference_to_food_import(plan.reference)
                    )
                food, created = promote_food_import(
                    session,
                    food_import.id,
                    PromoteFoodImportCommand(
                        catalog_key=plan.response.catalog_key or "",
                        name=plan.reference.description,
                    ),
                )
                promoted += int(created)
                created_foods[plan.reference.external_id] = food
            else:
                reused_foods += 1
            existing_alias = session.scalar(
                select(FoodAlias).where(
                    FoodAlias.normalized_alias == plan.response.normalized_name
                )
            )
            if existing_alias is None:
                apply_review_decision(
                    session,
                    plan.representative.recipe_import_id,
                    ReviewDecisionCommand(
                        action=ReviewDecisionAction.ADD_ALIAS,
                        ingredient_id=plan.representative.id,
                        food_key=food.catalog_key,
                        alias=plan.response.ingredient_name,
                    ),
                )
                aliases_added += 1
            resolved_items.append(
                replace(plan.response, status="resolved", food_id=food.id)
            )
        for recipe_import in session.scalars(
            select(RecipeImport).where(
                RecipeImport.status != RecipeImportStatus.REJECTED
            )
        ):
            recipe_import.status = RecipeImportStatus.RECEIVED
            process_recipe_import(session, recipe_import.id)
    else:
        resolved_items = [plan.response for plan in plans]
    ready_after = _ready_recipe_count(session)
    return AutoResolutionResult(
        dry_run=dry_run,
        unique_unknown_ingredients=len(grouped),
        processed=len(plans),
        eligible=sum(plan.response.status == "eligible" for plan in plans),
        promoted=promoted,
        aliases_added=aliases_added,
        reused_foods=reused_foods,
        ambiguous=sum(plan.response.status == "ambiguous" for plan in plans),
        no_match=sum(plan.response.status == "no_match" for plan in plans),
        incomplete=sum(
            plan.response.status == "incomplete_reference" for plan in plans
        ),
        conflicts=sum(plan.response.status == "conflict" for plan in plans),
        ready_recipes_before=ready_before,
        ready_recipes_after=ready_after,
        items=tuple(resolved_items),
    )


def canonical_catalog_key(ingredient_name: str, external_id: str) -> str:
    ascii_name = unicodedata.normalize("NFKD", ingredient_name).encode(
        "ascii", "ignore"
    ).decode("ascii")
    tokens = [_singular(token) for token in normalize_text(ascii_name).split()]
    key = re.sub(r"[^a-z0-9_]+", "", "_".join(tokens))[:100].strip("_")
    return key or f"fdc_{external_id}"


def _is_complete(item: FoodReferenceItem) -> bool:
    return all(
        value is not None
        for value in (
            item.calories_per_100,
            item.protein_per_100,
            item.carbs_per_100,
            item.fat_per_100,
        )
    )


def _ready_recipe_count(session: Session) -> int:
    return len(
        tuple(
            session.scalars(
                select(RecipeImport.id).where(
                    RecipeImport.status
                    == RecipeImportStatus.READY_FOR_CATALOG_REVIEW
                )
            )
        )
    )


def _singular(token: str) -> str:
    if len(token) > 4 and token.endswith("ies"):
        return f"{token[:-3]}y"
    if len(token) > 4 and token.endswith("oes"):
        return token[:-2]
    if len(token) > 3 and token.endswith("s") and not token.endswith("ss"):
        return token[:-1]
    return token
