import hashlib
import json
import re
import unicodedata
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from preppilot_api.models import (
    Food,
    FoodAlias,
    FoodMeasureDefault,
    ImportedIngredientStatus,
    ImportReviewDecision,
    ImportReviewReason,
    MeasurementUnit,
    RecipeImport,
    RecipeImportIngredient,
    RecipeImportStatus,
    ReviewDecisionAction,
)


class ImportModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ExternalIngredientPayload(ImportModel):
    line: str = Field(min_length=1)
    name: str = Field(min_length=1)
    amount: str | None = None
    unit: str | None = None


class ExternalRecipePayload(ImportModel):
    title: str = Field(min_length=1)
    servings: str | None = None
    instructions: str = Field(min_length=1)
    ingredients: tuple[ExternalIngredientPayload, ...] = Field(min_length=1)


class CreateRecipeImportCommand(ImportModel):
    source_name: str = Field(min_length=1, max_length=100)
    external_id: str = Field(min_length=1, max_length=200)
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    payload: ExternalRecipePayload


class ReviewDecisionCommand(ImportModel):
    action: ReviewDecisionAction
    ingredient_id: int | None = None
    food_key: str | None = None
    alias: str | None = None
    amount: Decimal | None = Field(default=None, gt=0)
    measure_key: str | None = None
    source_name: str | None = None
    source_reference: str | None = None


class RecipeImportNotFoundError(LookupError):
    pass


class RecipeImportDecisionError(ValueError):
    pass


_MASS_UNITS = {
    "g": Decimal("1"),
    "gram": Decimal("1"),
    "grams": Decimal("1"),
    "gramm": Decimal("1"),
    "kg": Decimal("1000"),
    "kilogram": Decimal("1000"),
    "kilograms": Decimal("1000"),
    "kilogramm": Decimal("1000"),
}
_VOLUME_UNITS = {
    "ml": Decimal("1"),
    "milliliter": Decimal("1"),
    "milliliters": Decimal("1"),
    "l": Decimal("1000"),
    "liter": Decimal("1000"),
    "liters": Decimal("1000"),
    "litre": Decimal("1000"),
    "litres": Decimal("1000"),
}
_SPOON_UNITS = {
    "tsp": Decimal("5"),
    "teaspoon": Decimal("5"),
    "teaspoons": Decimal("5"),
    "tl": Decimal("5"),
    "tbsp": Decimal("15"),
    "tablespoon": Decimal("15"),
    "tablespoons": Decimal("15"),
    "el": Decimal("15"),
}
_MEASURE_ALIASES = {
    "piece": "piece",
    "pieces": "piece",
    "pc": "piece",
    "pcs": "piece",
    "stück": "piece",
    "egg": "egg",
    "eggs": "egg",
    "ei": "egg",
    "eier": "egg",
    "clove": "clove",
    "cloves": "clove",
    "zehe": "clove",
    "zehen": "clove",
    "slice": "slice",
    "slices": "slice",
    "scheibe": "slice",
    "scheiben": "slice",
}
_THREE_PLACES = Decimal("0.001")


def create_recipe_import(
    session: Session, command: CreateRecipeImportCommand
) -> tuple[RecipeImport, bool]:
    raw_payload = command.payload.model_dump(mode="json")
    content_hash = _content_hash(raw_payload)
    existing = session.scalar(
        select(RecipeImport).where(
            RecipeImport.source_name == command.source_name.strip(),
            RecipeImport.external_id == command.external_id.strip(),
            RecipeImport.content_hash == content_hash,
        )
    )
    if existing is not None:
        return existing, False

    recipe_import = RecipeImport(
        source_name=command.source_name.strip(),
        external_id=command.external_id.strip(),
        fetched_at=command.fetched_at,
        raw_payload=raw_payload,
        content_hash=content_hash,
        raw_servings=command.payload.servings,
        manual_servings=None,
        status=RecipeImportStatus.RECEIVED,
    )
    session.add(recipe_import)
    session.flush()
    session.add_all(
        RecipeImportIngredient(
            recipe_import_id=recipe_import.id,
            position=position,
            raw_line=ingredient.line,
            raw_name=ingredient.name,
            raw_amount=ingredient.amount,
            raw_unit=ingredient.unit,
            status=ImportedIngredientStatus.NEEDS_REVIEW,
            review_reason=None,
            food_id=None,
            manual_food_id=None,
            normalized_amount=None,
            manual_amount=None,
            excluded=False,
        )
        for position, ingredient in enumerate(command.payload.ingredients)
    )
    session.flush()
    process_recipe_import(session, recipe_import.id)
    return recipe_import, True


def process_recipe_import(session: Session, recipe_import_id: int) -> RecipeImport:
    recipe_import = get_recipe_import(session, recipe_import_id)
    if recipe_import.status == RecipeImportStatus.REJECTED:
        return recipe_import

    ingredients = _ingredients_for_import(session, recipe_import.id)
    servings = _positive_decimal(
        str(recipe_import.manual_servings)
        if recipe_import.manual_servings is not None
        else recipe_import.raw_servings
    )
    foods = tuple(session.scalars(select(Food).order_by(Food.id)))
    foods_by_id = {food.id: food for food in foods}
    food_matches: dict[str, list[Food]] = {}
    for food in foods:
        for candidate in (food.name, food.catalog_key):
            food_matches.setdefault(normalize_text(candidate), []).append(food)
    for alias in session.scalars(select(FoodAlias).order_by(FoodAlias.id)):
        alias_food = foods_by_id.get(alias.food_id)
        if alias_food is not None:
            food_matches.setdefault(alias.normalized_alias, []).append(alias_food)

    measure_defaults = {
        (default.food_id, default.measure_key): default.amount
        for default in session.scalars(select(FoodMeasureDefault))
    }

    for ingredient in ingredients:
        _process_ingredient(
            ingredient,
            servings,
            foods_by_id,
            food_matches,
            measure_defaults,
        )

    normalized_count = sum(
        ingredient.status == ImportedIngredientStatus.NORMALIZED
        for ingredient in ingredients
    )
    all_complete = all(
        ingredient.status
        in (ImportedIngredientStatus.NORMALIZED, ImportedIngredientStatus.EXCLUDED)
        for ingredient in ingredients
    )
    recipe_import.status = (
        RecipeImportStatus.READY_FOR_CATALOG_REVIEW
        if all_complete and normalized_count > 0
        else RecipeImportStatus.NEEDS_REVIEW
    )
    session.flush()
    return recipe_import


def apply_review_decision(
    session: Session,
    recipe_import_id: int,
    command: ReviewDecisionCommand,
) -> RecipeImport:
    recipe_import = get_recipe_import(session, recipe_import_id)
    ingredient = _decision_ingredient(session, recipe_import, command)
    details: dict[str, object] = {}

    if command.action == ReviewDecisionAction.SET_SERVINGS:
        if command.ingredient_id is not None or command.amount is None:
            raise RecipeImportDecisionError(
                "set_servings requires amount and no ingredient_id"
            )
        recipe_import.manual_servings = command.amount
        details["servings"] = str(command.amount)
    elif command.action == ReviewDecisionAction.REJECT:
        if command.ingredient_id is not None:
            raise RecipeImportDecisionError("reject does not accept ingredient_id")
        recipe_import.status = RecipeImportStatus.REJECTED
    elif ingredient is None:
        raise RecipeImportDecisionError(
            f"{command.action.value} requires an ingredient_id"
        )
    elif command.action == ReviewDecisionAction.ASSIGN_FOOD:
        food = _required_food(session, command.food_key)
        ingredient.manual_food_id = food.id
        ingredient.excluded = False
        details["food_key"] = food.catalog_key
    elif command.action == ReviewDecisionAction.ADD_ALIAS:
        food = _required_food(session, command.food_key)
        alias_value = (command.alias or ingredient.raw_name).strip()
        normalized_alias = normalize_text(alias_value)
        if not normalized_alias:
            raise RecipeImportDecisionError("alias must not be blank")
        existing_alias = session.scalar(
            select(FoodAlias).where(FoodAlias.normalized_alias == normalized_alias)
        )
        if existing_alias is not None and existing_alias.food_id != food.id:
            raise RecipeImportDecisionError("alias already belongs to another food")
        conflicting_food = next(
            (
                candidate
                for candidate in session.scalars(select(Food))
                if candidate.id != food.id
                and normalized_alias
                in {
                    normalize_text(candidate.name),
                    normalize_text(candidate.catalog_key),
                }
            ),
            None,
        )
        if conflicting_food is not None:
            raise RecipeImportDecisionError(
                "alias conflicts with another internal food"
            )
        if existing_alias is None:
            session.add(
                FoodAlias(
                    alias=alias_value,
                    normalized_alias=normalized_alias,
                    food_id=food.id,
                    source_name=recipe_import.source_name,
                )
            )
        ingredient.manual_food_id = None
        ingredient.excluded = False
        details.update(alias=alias_value, food_key=food.catalog_key)
    elif command.action == ReviewDecisionAction.ADD_MEASURE_DEFAULT:
        food = _required_food(session, command.food_key)
        if command.amount is None or not command.source_name:
            raise RecipeImportDecisionError(
                "add_measure_default requires amount, food_key and source_name"
            )
        raw_measure = command.measure_key or ingredient.raw_unit
        measure_key = canonical_measure(raw_measure)
        if not measure_key:
            raise RecipeImportDecisionError("measure_key must not be blank")
        existing_default = session.scalar(
            select(FoodMeasureDefault).where(
                FoodMeasureDefault.food_id == food.id,
                FoodMeasureDefault.measure_key == measure_key,
            )
        )
        if existing_default is not None:
            raise RecipeImportDecisionError("measure default already exists")
        session.add(
            FoodMeasureDefault(
                food_id=food.id,
                measure_key=measure_key,
                amount=command.amount,
                source_name=command.source_name.strip(),
                source_reference=command.source_reference,
            )
        )
        ingredient.manual_food_id = food.id
        ingredient.excluded = False
        details.update(
            food_key=food.catalog_key,
            measure_key=measure_key,
            amount=str(command.amount),
            source_name=command.source_name.strip(),
        )
    elif command.action == ReviewDecisionAction.OVERRIDE_AMOUNT:
        if command.amount is None:
            raise RecipeImportDecisionError("override_amount requires amount")
        if command.food_key is not None:
            ingredient.manual_food_id = _required_food(session, command.food_key).id
        ingredient.manual_amount = command.amount
        ingredient.excluded = False
        details["amount"] = str(command.amount)
        if command.food_key is not None:
            details["food_key"] = command.food_key
    elif command.action == ReviewDecisionAction.EXCLUDE:
        other_active = session.scalar(
            select(RecipeImportIngredient.id).where(
                RecipeImportIngredient.recipe_import_id == recipe_import.id,
                RecipeImportIngredient.id != ingredient.id,
                RecipeImportIngredient.excluded.is_(False),
            )
        )
        if other_active is None:
            raise RecipeImportDecisionError("the final ingredient cannot be excluded")
        ingredient.excluded = True
        ingredient.manual_amount = None
        ingredient.manual_food_id = None
    else:
        raise RecipeImportDecisionError("unsupported review decision")

    session.flush()
    session.add(
        ImportReviewDecision(
            recipe_import_id=recipe_import.id,
            ingredient_id=None if ingredient is None else ingredient.id,
            action=command.action,
            details=details,
            created_at=datetime.now(UTC),
        )
    )
    if command.action != ReviewDecisionAction.REJECT:
        recipe_import.status = RecipeImportStatus.RECEIVED
        session.flush()
        process_recipe_import(session, recipe_import.id)
    return recipe_import


def get_recipe_import(session: Session, recipe_import_id: int) -> RecipeImport:
    recipe_import = session.get(RecipeImport, recipe_import_id)
    if recipe_import is None:
        raise RecipeImportNotFoundError(recipe_import_id)
    return recipe_import


def list_recipe_imports(
    session: Session, status: RecipeImportStatus | None = None
) -> tuple[RecipeImport, ...]:
    statement = select(RecipeImport).order_by(RecipeImport.id)
    if status is not None:
        statement = statement.where(RecipeImport.status == status)
    return tuple(session.scalars(statement))


def ingredients_for_import(
    session: Session, recipe_import_id: int
) -> tuple[RecipeImportIngredient, ...]:
    get_recipe_import(session, recipe_import_id)
    return _ingredients_for_import(session, recipe_import_id)


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return " ".join(re.sub(r"[^\w]+", " ", normalized).split())


def canonical_measure(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = normalize_text(value)
    if not normalized:
        return None
    return _MEASURE_ALIASES.get(normalized, normalized)


def _content_hash(raw_payload: dict[str, object]) -> str:
    serialized = json.dumps(
        raw_payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _positive_decimal(value: str | None) -> Decimal | None:
    if value is None:
        return None
    try:
        number = Decimal(value.strip().replace(",", "."))
    except InvalidOperation, AttributeError:
        return None
    if not number.is_finite() or number <= 0:
        return None
    return number


def _ingredients_for_import(
    session: Session, recipe_import_id: int
) -> tuple[RecipeImportIngredient, ...]:
    return tuple(
        session.scalars(
            select(RecipeImportIngredient)
            .where(RecipeImportIngredient.recipe_import_id == recipe_import_id)
            .order_by(RecipeImportIngredient.position)
        )
    )


def _process_ingredient(
    ingredient: RecipeImportIngredient,
    servings: Decimal | None,
    foods_by_id: dict[int, Food],
    food_matches: dict[str, list[Food]],
    measure_defaults: dict[tuple[int, str], Decimal],
) -> None:
    ingredient.food_id = None
    ingredient.normalized_amount = None
    ingredient.review_reason = None
    if ingredient.excluded:
        ingredient.status = ImportedIngredientStatus.EXCLUDED
        return

    food: Food | None = None
    if ingredient.manual_food_id is not None:
        food = foods_by_id.get(ingredient.manual_food_id)
    else:
        matches = {
            candidate.id: candidate
            for candidate in food_matches.get(normalize_text(ingredient.raw_name), [])
        }
        if len(matches) > 1:
            _mark_review(ingredient, ImportReviewReason.AMBIGUOUS_FOOD)
            return
        if matches:
            food = next(iter(matches.values()))
    if food is None:
        _mark_review(ingredient, ImportReviewReason.UNKNOWN_FOOD)
        return

    ingredient.food_id = food.id
    if servings is None:
        _mark_review(ingredient, ImportReviewReason.MISSING_SERVING_COUNT)
        return
    if ingredient.manual_amount is not None:
        ingredient.normalized_amount = ingredient.manual_amount.quantize(
            _THREE_PLACES, rounding=ROUND_HALF_UP
        )
        ingredient.status = ImportedIngredientStatus.NORMALIZED
        return

    raw_amount = _positive_decimal(ingredient.raw_amount)
    if raw_amount is None:
        _mark_review(ingredient, ImportReviewReason.INVALID_OR_RANGED_QUANTITY)
        return
    total_amount, reason = _normalize_total_amount(
        raw_amount,
        ingredient.raw_unit,
        food,
        measure_defaults,
    )
    if reason is not None or total_amount is None:
        _mark_review(ingredient, reason or ImportReviewReason.UNSUPPORTED_UNIT)
        return
    ingredient.normalized_amount = (total_amount / servings).quantize(
        _THREE_PLACES, rounding=ROUND_HALF_UP
    )
    ingredient.status = ImportedIngredientStatus.NORMALIZED


def _normalize_total_amount(
    amount: Decimal,
    raw_unit: str | None,
    food: Food,
    measure_defaults: dict[tuple[int, str], Decimal],
) -> tuple[Decimal | None, ImportReviewReason | None]:
    unit = normalize_text(raw_unit or "")
    if unit in _MASS_UNITS:
        if food.unit != MeasurementUnit.GRAM:
            return None, ImportReviewReason.INCOMPATIBLE_MEASUREMENT
        return amount * _MASS_UNITS[unit], None
    if unit in _VOLUME_UNITS:
        if food.unit != MeasurementUnit.MILLILITER:
            return None, ImportReviewReason.INCOMPATIBLE_MEASUREMENT
        return amount * _VOLUME_UNITS[unit], None
    if unit in _SPOON_UNITS:
        return amount * _SPOON_UNITS[unit], None

    measure_key = canonical_measure(raw_unit)
    if measure_key is None:
        return None, ImportReviewReason.UNSUPPORTED_UNIT
    default_amount = measure_defaults.get((food.id, measure_key))
    if default_amount is not None:
        return amount * default_amount, None
    if measure_key in set(_MEASURE_ALIASES.values()):
        return None, ImportReviewReason.MISSING_MEASURE_DEFAULT
    return None, ImportReviewReason.UNSUPPORTED_UNIT


def _mark_review(
    ingredient: RecipeImportIngredient, reason: ImportReviewReason
) -> None:
    ingredient.status = ImportedIngredientStatus.NEEDS_REVIEW
    ingredient.review_reason = reason
    ingredient.normalized_amount = None


def _decision_ingredient(
    session: Session,
    recipe_import: RecipeImport,
    command: ReviewDecisionCommand,
) -> RecipeImportIngredient | None:
    if command.ingredient_id is None:
        return None
    ingredient = session.get(RecipeImportIngredient, command.ingredient_id)
    if ingredient is None or ingredient.recipe_import_id != recipe_import.id:
        raise RecipeImportDecisionError("ingredient does not belong to recipe import")
    return ingredient


def _required_food(session: Session, food_key: str | None) -> Food:
    if food_key is None:
        raise RecipeImportDecisionError("food_key is required")
    food = session.scalar(select(Food).where(Food.catalog_key == food_key))
    if food is None:
        raise RecipeImportDecisionError(f"unknown food_key: {food_key}")
    return food
