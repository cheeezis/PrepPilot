from dataclasses import dataclass
from decimal import Decimal

import httpx2
from pydantic import BaseModel, ConfigDict, Field


@dataclass(frozen=True)
class FoodSearchCandidate:
    fdc_id: int
    description: str
    data_type: str


@dataclass(frozen=True)
class FoodNutrients:
    calories: Decimal | None
    protein: Decimal | None
    carbs: Decimal | None
    fat: Decimal | None


@dataclass(frozen=True)
class FdcFoodPortion:
    source_id: int
    amount: Decimal
    gram_weight: Decimal
    unit: str
    modifier: str | None


@dataclass(frozen=True)
class FoodDetails:
    fdc_id: int
    description: str
    data_type: str
    nutrients_per_100g: FoodNutrients
    portions: tuple[FdcFoodPortion, ...] = ()


class _ApiModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


class _SearchFood(_ApiModel):
    fdc_id: int = Field(alias="fdcId")
    description: str
    data_type: str = Field(alias="dataType")


class _SearchResponse(_ApiModel):
    foods: list[_SearchFood]


class _NutrientDefinition(_ApiModel):
    id: int
    unit_name: str = Field(alias="unitName")


class _FoodNutrient(_ApiModel):
    nutrient: _NutrientDefinition
    amount: Decimal | None = None


class _MeasureUnit(_ApiModel):
    name: str


class _FoodPortion(_ApiModel):
    id: int
    amount: Decimal
    gram_weight: Decimal = Field(alias="gramWeight")
    measure_unit: _MeasureUnit = Field(alias="measureUnit")
    modifier: str | None = None


class _FoodDetailsResponse(_ApiModel):
    fdc_id: int = Field(alias="fdcId")
    description: str
    data_type: str = Field(alias="dataType")
    food_nutrients: list[_FoodNutrient] = Field(alias="foodNutrients")
    food_portions: list[_FoodPortion] = Field(
        alias="foodPortions", default_factory=list
    )


class FoodDataCentralClient:
    _BASE_URL = "https://api.nal.usda.gov/fdc/v1"
    _GENERIC_DATA_TYPES = ["Foundation", "SR Legacy"]

    def __init__(self, api_key: str, http_client: httpx2.Client | None = None) -> None:
        if not api_key.strip():
            raise ValueError("FoodData Central API key must not be blank")
        self._api_key = api_key
        self._http_client = http_client or httpx2.Client(timeout=10)
        self._owns_http_client = http_client is None

    def __enter__(self) -> "FoodDataCentralClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        if self._owns_http_client:
            self._http_client.close()

    def search_foods(self, query: str) -> list[FoodSearchCandidate]:
        response = self._http_client.post(
            f"{self._BASE_URL}/foods/search",
            params={"api_key": self._api_key},
            json={
                "query": query,
                "dataType": self._GENERIC_DATA_TYPES,
                "pageSize": 10,
            },
        )
        response.raise_for_status()
        parsed = _SearchResponse.model_validate(response.json())
        return [
            FoodSearchCandidate(
                fdc_id=food.fdc_id,
                description=food.description,
                data_type=food.data_type,
            )
            for food in parsed.foods
        ]

    def get_food(self, fdc_id: int) -> FoodDetails:
        response = self._http_client.get(
            f"{self._BASE_URL}/food/{fdc_id}",
            params={"api_key": self._api_key},
        )
        response.raise_for_status()
        parsed = _FoodDetailsResponse.model_validate(response.json())
        nutrients = {
            item.nutrient.id: item.amount
            for item in parsed.food_nutrients
            if item.amount is not None
        }
        return FoodDetails(
            fdc_id=parsed.fdc_id,
            description=parsed.description,
            data_type=parsed.data_type,
            nutrients_per_100g=FoodNutrients(
                calories=_first_present(nutrients, 1008, 2047, 2048),
                protein=nutrients.get(1003),
                carbs=nutrients.get(1005),
                fat=nutrients.get(1004),
            ),
            portions=tuple(
                _normalize_portion(portion) for portion in parsed.food_portions
            ),
        )


def _first_present(nutrients: dict[int, Decimal], *nutrient_ids: int) -> Decimal | None:
    for nutrient_id in nutrient_ids:
        if nutrient_id in nutrients:
            return nutrients[nutrient_id]
    return None


def _clean_optional(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _normalize_portion(portion: _FoodPortion) -> FdcFoodPortion:
    measure_unit = portion.measure_unit.name.strip().casefold()
    modifier = (_clean_optional(portion.modifier) or "").casefold()
    amount = portion.amount

    if modifier == "half":
        return FdcFoodPortion(
            source_id=portion.id,
            amount=amount / Decimal("2"),
            gram_weight=portion.gram_weight,
            unit="piece",
            modifier=None,
        )

    unit, normalized_modifier = _parse_portion_description(modifier)
    if unit is None:
        unit = _normalize_portion_unit(measure_unit)
        normalized_modifier = _clean_optional(portion.modifier)
    return FdcFoodPortion(
        source_id=portion.id,
        amount=amount,
        gram_weight=portion.gram_weight,
        unit=unit,
        modifier=normalized_modifier,
    )


def _parse_portion_description(description: str) -> tuple[str | None, str | None]:
    prefixes = {
        "tablespoon": "tbsp",
        "tbsp": "tbsp",
        "teaspoon": "tsp",
        "tsp": "tsp",
        "cup": "cup",
        "sprig": "sprig",
        "sprigs": "sprig",
        "slice": "slice",
        "slices": "slice",
        "ring": "ring",
        "rings": "ring",
        "clove": "piece",
        "cloves": "piece",
    }
    for prefix, unit in prefixes.items():
        if description == prefix:
            modifier = "clove" if prefix.startswith("clove") else None
            return unit, modifier
        if description.startswith(f"{prefix},") or description.startswith(f"{prefix} "):
            remainder = description[len(prefix) :].lstrip(" ,")
            return unit, remainder or None

    for size in ("small", "medium", "large"):
        if description == size or description.startswith(f"{size} "):
            return "piece", size
    return None, None


def _normalize_portion_unit(unit: str) -> str:
    aliases = {
        "tablespoon": "tbsp",
        "teaspoon": "tsp",
    }
    return aliases.get(unit, unit or "other")
