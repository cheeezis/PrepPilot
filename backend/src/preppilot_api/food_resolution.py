import re
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Mapping, Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from preppilot_api.food_data_central import (
    FdcFoodPortion,
    FoodDetails,
    FoodSearchCandidate,
)
from preppilot_api.ingredient_names import normalize_ingredient_name
from preppilot_api.models import Food, FoodAlias, FoodPortion, MeasurementUnit


class FoodResolutionError(ValueError):
    pass


class AmbiguousFoodError(FoodResolutionError):
    pass


class IncompleteFoodDataError(FoodResolutionError):
    pass


class FoodDataSource(Protocol):
    def search_foods(self, query: str) -> list[FoodSearchCandidate]: ...

    def get_food(self, fdc_id: int) -> FoodDetails: ...


@dataclass(frozen=True)
class CatalogFoodDefinition:
    name: str
    unit: MeasurementUnit
    calories_per_100: Decimal
    protein_per_100: Decimal
    carbs_per_100: Decimal
    fat_per_100: Decimal
    source_name: str
    source_reference: str


@dataclass(frozen=True)
class CatalogPortionDefinition:
    amount: Decimal
    unit: str
    modifier: str | None
    gram_weight: Decimal
    source_name: str
    source_reference: str | None


_WORDS = re.compile(r"[a-z0-9]+")
_PREPARATION_WORDS = {
    "breaded",
    "canned",
    "cooked",
    "dehydrated",
    "dried",
    "flour",
    "fried",
    "grilled",
    "powder",
    "roasted",
    "sauteed",
    "skin",
    "smoked",
}


class FoodResolver:
    def __init__(
        self,
        data_source: FoodDataSource,
        preferred_fdc_ids: Mapping[tuple[str, str], int] | None = None,
        catalog_foods: Mapping[tuple[str, str], CatalogFoodDefinition] | None = None,
        catalog_portions: Mapping[tuple[str, str], tuple[CatalogPortionDefinition, ...]]
        | None = None,
    ) -> None:
        self._data_source = data_source
        self._preferred_fdc_ids = preferred_fdc_ids or {}
        self._catalog_foods = catalog_foods or {}
        self._catalog_portions = catalog_portions or {}

    def resolve(self, session: Session, source_name: str, external_name: str) -> Food:
        normalized_source = source_name.strip().casefold()
        if not normalized_source:
            raise ValueError("Source name must not be blank")
        normalized_name = normalize_ingredient_name(external_name)

        alias = session.get(FoodAlias, (normalized_source, normalized_name))
        if alias is not None:
            food = session.get(Food, alias.food_id)
            if food is None:  # The foreign key should make this impossible.
                raise FoodResolutionError("Food alias references a missing food")
            _add_missing_catalog_portions(
                session,
                food.id,
                self._catalog_portions.get((normalized_source, normalized_name), ()),
            )
            return food

        catalog_food = self._catalog_foods.get((normalized_source, normalized_name))
        if catalog_food is not None:
            return _store_food_and_alias(
                session,
                food=_create_catalog_food(catalog_food),
                source_name=normalized_source,
                external_name=external_name,
                normalized_name=normalized_name,
                catalog_portions=self._catalog_portions.get(
                    (normalized_source, normalized_name), ()
                ),
            )

        preferred_fdc_id = self._preferred_fdc_ids.get(
            (normalized_source, normalized_name)
        )
        if preferred_fdc_id is None:
            candidates = self._data_source.search_foods(normalized_name)
            preferred_fdc_id = _select_candidate(normalized_name, candidates).fdc_id
        details = self._data_source.get_food(preferred_fdc_id)
        return _store_food_and_alias(
            session,
            food=_create_food(details),
            source_name=normalized_source,
            external_name=external_name,
            normalized_name=normalized_name,
            fdc_portions=details.portions,
            catalog_portions=self._catalog_portions.get(
                (normalized_source, normalized_name), ()
            ),
        )


def _store_food_and_alias(
    session: Session,
    food: Food,
    source_name: str,
    external_name: str,
    normalized_name: str,
    fdc_portions: tuple[FdcFoodPortion, ...] = (),
    catalog_portions: tuple[CatalogPortionDefinition, ...] = (),
) -> Food:
    session.add(food)
    session.flush()
    session.add(
        FoodAlias(
            source_name=source_name,
            external_name=external_name.strip(),
            normalized_name=normalized_name,
            food_id=food.id,
        )
    )
    retrieved_at = datetime.now(UTC)
    session.add_all(
        FoodPortion(
            food_id=food.id,
            amount=portion.amount,
            unit=portion.unit,
            modifier=portion.modifier,
            gram_weight=portion.gram_weight,
            source_name="food_data_central",
            source_reference=str(portion.source_id),
            source_retrieved_at=retrieved_at,
        )
        for portion in fdc_portions
    )
    _add_missing_catalog_portions(session, food.id, catalog_portions)
    return food


def _add_missing_catalog_portions(
    session: Session,
    food_id: int,
    definitions: tuple[CatalogPortionDefinition, ...],
) -> None:
    existing = {
        (portion.unit, portion.modifier, portion.source_name)
        for portion in session.scalars(
            select(FoodPortion).where(FoodPortion.food_id == food_id)
        )
    }
    retrieved_at = datetime.now(UTC)
    for definition in definitions:
        identity = (definition.unit, definition.modifier, definition.source_name)
        if identity in existing:
            continue
        session.add(
            FoodPortion(
                food_id=food_id,
                amount=definition.amount,
                unit=definition.unit,
                modifier=definition.modifier,
                gram_weight=definition.gram_weight,
                source_name=definition.source_name,
                source_reference=definition.source_reference,
                source_retrieved_at=retrieved_at,
            )
        )
        existing.add(identity)


def _select_candidate(
    query: str, candidates: list[FoodSearchCandidate]
) -> FoodSearchCandidate:
    query_words = _word_set(query)
    ranked: list[tuple[int, FoodSearchCandidate]] = []
    for candidate in candidates:
        description_words = _word_set(candidate.description)
        if not query_words <= description_words:
            continue
        unwanted_words = (_PREPARATION_WORDS - query_words) & description_words
        if unwanted_words:
            continue

        score = 10 * len(query_words)
        score += 1 if candidate.data_type == "Foundation" else 0
        score += 2 if "raw" in description_words else 0
        score += 1 if "skinless" in description_words else 0
        score -= 2 * len(description_words - query_words)
        ranked.append((score, candidate))

    ranked.sort(key=lambda item: (-item[0], item[1].fdc_id))
    if not ranked:
        raise FoodResolutionError(f"No reliable food candidate found for {query!r}")
    if len(ranked) > 1 and ranked[0][0] == ranked[1][0]:
        raise AmbiguousFoodError(f"Food candidates are ambiguous for {query!r}")
    return ranked[0][1]


def _create_food(details: FoodDetails) -> Food:
    nutrients = details.nutrients_per_100g
    values = (nutrients.calories, nutrients.protein, nutrients.carbs, nutrients.fat)
    if any(value is None for value in values):
        raise IncompleteFoodDataError(
            f"FoodData Central food {details.fdc_id} has incomplete MVP nutrients"
        )

    assert nutrients.calories is not None
    assert nutrients.protein is not None
    assert nutrients.carbs is not None
    assert nutrients.fat is not None
    return Food(
        name=details.description,
        brand=None,
        unit=MeasurementUnit.GRAM,
        calories_per_100=nutrients.calories,
        protein_per_100=nutrients.protein,
        carbs_per_100=nutrients.carbs,
        fat_per_100=nutrients.fat,
        source_name="food_data_central",
        source_reference=str(details.fdc_id),
        source_retrieved_at=datetime.now(UTC),
    )


def _create_catalog_food(definition: CatalogFoodDefinition) -> Food:
    return Food(
        name=definition.name,
        brand=None,
        unit=definition.unit,
        calories_per_100=definition.calories_per_100,
        protein_per_100=definition.protein_per_100,
        carbs_per_100=definition.carbs_per_100,
        fat_per_100=definition.fat_per_100,
        source_name=definition.source_name,
        source_reference=definition.source_reference,
        source_retrieved_at=datetime.now(UTC),
    )


def _word_set(value: str) -> set[str]:
    return {
        _canonical_search_word(word)
        for word in _WORDS.findall(normalize_ingredient_name(value))
    }


def _canonical_search_word(word: str) -> str:
    if word.endswith("ies") and len(word) > 3:
        return f"{word[:-3]}y"
    if word.endswith("oes") and len(word) > 3:
        return word[:-2]
    if word.endswith("s") and not word.endswith("ss") and len(word) > 3:
        return word[:-1]
    return word
