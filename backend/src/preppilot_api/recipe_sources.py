import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from functools import lru_cache
from typing import Protocol, cast
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from preppilot_api.config import get_settings
from preppilot_api.recipe_imports import (
    CreateRecipeImportCommand,
    ExternalIngredientPayload,
    ExternalRecipePayload,
)

THEMEALDB_SOURCE_NAME = "themealdb"
_MEASURE_PATTERN = re.compile(
    r"^(?P<amount>\d+\s+\d+/\d+|\d+/\d+|\d+(?:[.,]\d+)?)\s*(?P<unit>.*)$"
)


class RecipeSourceError(RuntimeError):
    pass


class RecipeSourceNotFoundError(RecipeSourceError):
    pass


class RecipeSourcePayloadError(RecipeSourceError):
    pass


class RecipeSourceUnavailableError(RecipeSourceError):
    pass


class JsonFetcher(Protocol):
    def __call__(self, url: str, timeout: float) -> dict[str, object]: ...


@dataclass(frozen=True)
class FetchedRecipe:
    command: CreateRecipeImportCommand
    source_payload: dict[str, object]


@dataclass(frozen=True)
class RecipeReference:
    external_id: str
    name: str


@dataclass(frozen=True)
class TheMealDbSource:
    api_key: str
    base_url: str
    timeout_seconds: float
    fetch_json: JsonFetcher

    def discover_category(
        self, category: str, *, limit: int
    ) -> tuple[RecipeReference, ...]:
        normalized_category = category.strip()
        if not normalized_category:
            raise RecipeSourcePayloadError("TheMealDB category must not be blank")
        if not 1 <= limit <= 25:
            raise RecipeSourcePayloadError("TheMealDB batch limit must be between 1 and 25")
        url = (
            f"{self.base_url.rstrip('/')}/{quote(self.api_key, safe='')}"
            f"/filter.php?c={quote(normalized_category, safe='')}"
        )
        envelope = self.fetch_json(url, self.timeout_seconds)
        meals = envelope.get("meals")
        if meals is None:
            return ()
        if not isinstance(meals, list):
            raise RecipeSourcePayloadError("unexpected TheMealDB category response")

        references: list[RecipeReference] = []
        seen_ids: set[str] = set()
        for meal_value in meals:
            if not isinstance(meal_value, dict):
                raise RecipeSourcePayloadError(
                    "unexpected TheMealDB category meal payload"
                )
            meal = cast(dict[str, object], meal_value)
            meal_id = _required_text(meal, "idMeal")
            if not meal_id.isdecimal():
                raise RecipeSourcePayloadError("invalid TheMealDB category meal ID")
            if meal_id in seen_ids:
                continue
            seen_ids.add(meal_id)
            references.append(
                RecipeReference(
                    external_id=meal_id,
                    name=_required_text(meal, "strMeal"),
                )
            )
            if len(references) == limit:
                break
        return tuple(references)

    def fetch(self, external_id: str) -> FetchedRecipe:
        meal_id = external_id.strip()
        if not meal_id.isdecimal():
            raise RecipeSourcePayloadError("TheMealDB recipe ID must be numeric")
        url = (
            f"{self.base_url.rstrip('/')}/{quote(self.api_key, safe='')}"
            f"/lookup.php?i={quote(meal_id, safe='')}"
        )
        envelope = self.fetch_json(url, self.timeout_seconds)
        meals = envelope.get("meals")
        if meals is None:
            raise RecipeSourceNotFoundError(meal_id)
        if not isinstance(meals, list) or len(meals) != 1:
            raise RecipeSourcePayloadError("unexpected TheMealDB response")
        meal_value = meals[0]
        if not isinstance(meal_value, dict):
            raise RecipeSourcePayloadError("unexpected TheMealDB meal payload")
        meal = cast(dict[str, object], meal_value)
        returned_id = _required_text(meal, "idMeal")
        if returned_id != meal_id:
            raise RecipeSourcePayloadError("TheMealDB returned a different recipe ID")

        ingredients = _ingredients(meal)
        payload = ExternalRecipePayload(
            title=_required_text(meal, "strMeal"),
            servings=None,
            instructions=_required_text(meal, "strInstructions"),
            ingredients=ingredients,
        )
        return FetchedRecipe(
            command=CreateRecipeImportCommand(
                source_name=THEMEALDB_SOURCE_NAME,
                external_id=meal_id,
                fetched_at=datetime.now(UTC),
                payload=payload,
            ),
            source_payload=meal,
        )


def _ingredients(meal: dict[str, object]) -> tuple[ExternalIngredientPayload, ...]:
    ingredients: list[ExternalIngredientPayload] = []
    for position in range(1, 21):
        name = _optional_text(meal.get(f"strIngredient{position}"))
        measure = _optional_text(meal.get(f"strMeasure{position}"))
        if name is None:
            if measure is not None:
                raise RecipeSourcePayloadError("measure without ingredient")
            continue
        amount, unit = _split_measure(measure)
        line = " ".join(part for part in (measure, name) if part)
        ingredients.append(
            ExternalIngredientPayload(
                line=line or name,
                name=name,
                amount=amount,
                unit=unit,
            )
        )
    if not ingredients:
        raise RecipeSourcePayloadError("TheMealDB recipe has no ingredients")
    return tuple(ingredients)


def _split_measure(measure: str | None) -> tuple[str | None, str | None]:
    if measure is None:
        return None, None
    match = _MEASURE_PATTERN.fullmatch(measure)
    if match is None:
        return measure, None
    raw_amount = match.group("amount")
    unit = match.group("unit").strip() or None
    return _decimal_amount(raw_amount), unit


def _decimal_amount(value: str) -> str:
    parts = value.split()
    try:
        if len(parts) == 2:
            return str(Decimal(parts[0]) + _fraction(parts[1]))
        if "/" in value:
            return str(_fraction(value))
        return str(Decimal(value.replace(",", ".")))
    except (InvalidOperation, ZeroDivisionError) as error:
        raise RecipeSourcePayloadError("invalid TheMealDB measure") from error


def _fraction(value: str) -> Decimal:
    numerator, denominator = value.split("/", maxsplit=1)
    return Decimal(numerator) / Decimal(denominator)


def _required_text(payload: dict[str, object], key: str) -> str:
    value = _optional_text(payload.get(key))
    if value is None:
        raise RecipeSourcePayloadError(f"missing TheMealDB field: {key}")
    return value


def _optional_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def fetch_json(url: str, timeout: float) -> dict[str, object]:
    request = Request(url, headers={"User-Agent": "PrepPilot/0.1"})
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = json.load(response)
    except (HTTPError, URLError, TimeoutError, OSError) as error:
        raise RecipeSourceUnavailableError("TheMealDB request failed") from error
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise RecipeSourcePayloadError("TheMealDB returned invalid JSON") from error
    if not isinstance(payload, dict):
        raise RecipeSourcePayloadError("unexpected TheMealDB response")
    return cast(dict[str, object], payload)


@lru_cache
def get_themealdb_source() -> TheMealDbSource:
    settings = get_settings()
    return TheMealDbSource(
        api_key=settings.themealdb_api_key,
        base_url=settings.themealdb_base_url,
        timeout_seconds=settings.external_request_timeout_seconds,
        fetch_json=fetch_json,
    )
