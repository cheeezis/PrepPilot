from dataclasses import dataclass
from typing import Any

import httpx2
from pydantic import BaseModel, ConfigDict, Field


class MealNotFoundError(ValueError):
    pass


class MalformedMealResponseError(ValueError):
    pass


@dataclass(frozen=True)
class RecipeIngredient:
    name: str
    measure: str


@dataclass(frozen=True)
class Recipe:
    source_id: str
    name: str
    category: str | None
    area: str | None
    instructions: str
    original_source_url: str | None
    ingredients: tuple[RecipeIngredient, ...]


class _MealPayload(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    source_id: str = Field(alias="idMeal")
    name: str = Field(alias="strMeal")
    category: str | None = Field(alias="strCategory", default=None)
    area: str | None = Field(alias="strArea", default=None)
    instructions: str = Field(alias="strInstructions")
    original_source_url: str | None = Field(alias="strSource", default=None)


class _LookupResponse(BaseModel):
    meals: list[_MealPayload] | None


class TheMealDbClient:
    _BASE_URL = "https://www.themealdb.com/api/json/v1"
    _INGREDIENT_SLOTS = range(1, 21)

    def __init__(self, api_key: str, http_client: httpx2.Client | None = None) -> None:
        if not api_key.strip():
            raise ValueError("TheMealDB API key must not be blank")
        self._api_key = api_key
        self._http_client = http_client or httpx2.Client(timeout=10)
        self._owns_http_client = http_client is None

    def __enter__(self) -> "TheMealDbClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        if self._owns_http_client:
            self._http_client.close()

    def get_recipe(self, meal_id: str) -> Recipe:
        response = self._http_client.get(
            f"{self._BASE_URL}/{self._api_key}/lookup.php",
            params={"i": meal_id},
        )
        response.raise_for_status()
        parsed = _LookupResponse.model_validate(response.json())
        if not parsed.meals:
            raise MealNotFoundError(f"TheMealDB meal {meal_id!r} was not found")
        if len(parsed.meals) != 1:
            raise MalformedMealResponseError(
                f"Expected one TheMealDB meal for {meal_id!r}"
            )

        meal = parsed.meals[0]
        if meal.source_id != meal_id:
            raise MalformedMealResponseError(
                f"TheMealDB returned meal {meal.source_id!r} for {meal_id!r}"
            )
        return Recipe(
            source_id=meal.source_id,
            name=meal.name.strip(),
            category=_clean_optional(meal.category),
            area=_clean_optional(meal.area),
            instructions=meal.instructions.strip(),
            original_source_url=_clean_optional(meal.original_source_url),
            ingredients=_extract_ingredients(meal),
        )


def _extract_ingredients(meal: _MealPayload) -> tuple[RecipeIngredient, ...]:
    extra = meal.model_extra or {}
    ingredients: list[RecipeIngredient] = []
    for slot in TheMealDbClient._INGREDIENT_SLOTS:
        name = _clean_external_string(extra.get(f"strIngredient{slot}"))
        measure = _clean_external_string(extra.get(f"strMeasure{slot}"))
        if not name:
            if measure:
                raise MalformedMealResponseError(
                    f"TheMealDB ingredient slot {slot} has a measure but no name"
                )
            continue
        ingredients.append(RecipeIngredient(name=name, measure=measure or ""))
    return tuple(ingredients)


def _clean_external_string(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise MalformedMealResponseError("Expected a string in TheMealDB response")
    return _clean_optional(value)


def _clean_optional(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None
