import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from functools import lru_cache
from typing import Protocol, cast
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from preppilot_api.config import get_settings
from preppilot_api.food_imports import CreateFoodImportCommand

FOODDATA_CENTRAL_SOURCE_NAME = "fooddata_central"
_SUPPORTED_DATA_TYPES = {"Foundation", "SR Legacy"}
_NUTRIENT_IDS = {
    "calories": 1008,
    "protein": 1003,
    "fat": 1004,
    "total_carbs": 1005,
    "fiber": 1079,
}


class FoodSourceError(RuntimeError):
    pass


class FoodSourceNotFoundError(FoodSourceError):
    pass


class FoodSourcePayloadError(FoodSourceError):
    pass


class FoodSourceUnavailableError(FoodSourceError):
    pass


class JsonFetcher(Protocol):
    def __call__(self, url: str, timeout: float) -> dict[str, object]: ...


@dataclass(frozen=True)
class FoodSearchCandidate:
    external_id: str
    name: str
    data_type: str


@dataclass(frozen=True)
class FoodDataCentralSource:
    api_key: str
    base_url: str
    timeout_seconds: float
    fetch_json: JsonFetcher

    def search(
        self, ingredient_name: str, *, limit: int = 5
    ) -> tuple[FoodSearchCandidate, ...]:
        query_text = ingredient_name.strip()
        if not query_text:
            raise FoodSourcePayloadError("FoodData Central query must not be blank")
        if not 1 <= limit <= 10:
            raise FoodSourcePayloadError(
                "FoodData Central search limit must be between 1 and 10"
            )
        query = urlencode(
            {
                "api_key": self.api_key,
                "query": query_text,
                "dataType": "Foundation,SR Legacy",
                "pageSize": limit,
            }
        )
        url = f"{self.base_url.rstrip('/')}/foods/search?{query}"
        envelope = self.fetch_json(url, self.timeout_seconds)
        foods = envelope.get("foods")
        if not isinstance(foods, list):
            raise FoodSourcePayloadError("unexpected FoodData Central search response")

        candidates: list[FoodSearchCandidate] = []
        seen_ids: set[str] = set()
        for food_value in foods:
            if not isinstance(food_value, dict):
                raise FoodSourcePayloadError(
                    "unexpected FoodData Central search candidate"
                )
            food = cast(dict[str, object], food_value)
            external_id = str(food.get("fdcId", "")).strip()
            name = _text(food.get("description"))
            data_type = _text(food.get("dataType"))
            if (
                not external_id.isdecimal()
                or name is None
                or data_type not in _SUPPORTED_DATA_TYPES
            ):
                raise FoodSourcePayloadError(
                    "invalid FoodData Central search candidate"
                )
            if external_id in seen_ids:
                continue
            seen_ids.add(external_id)
            candidates.append(
                FoodSearchCandidate(
                    external_id=external_id,
                    name=name,
                    data_type=data_type,
                )
            )
        return tuple(candidates)

    def fetch(self, external_id: str) -> CreateFoodImportCommand:
        fdc_id = external_id.strip()
        if not fdc_id.isdecimal():
            raise FoodSourcePayloadError("FoodData Central ID must be numeric")
        query = urlencode({"api_key": self.api_key})
        url = f"{self.base_url.rstrip('/')}/food/{quote(fdc_id, safe='')}?{query}"
        payload = self.fetch_json(url, self.timeout_seconds)
        returned_id = payload.get("fdcId")
        if str(returned_id) != fdc_id:
            raise FoodSourcePayloadError("FoodData Central returned a different ID")

        reasons: list[str] = []
        data_type = _text(payload.get("dataType"))
        if data_type not in _SUPPORTED_DATA_TYPES:
            reasons.append("unsupported_data_type")
        name = _text(payload.get("description"))
        if name is None:
            reasons.append("missing_name")
        nutrients = _nutrients(payload, reasons)
        total_carbs = nutrients.get("total_carbs")
        fiber = nutrients.get("fiber")
        available_carbs: Decimal | None = None
        if total_carbs is not None and fiber is not None:
            available_carbs = total_carbs - fiber
            if available_carbs < 0:
                available_carbs = None
                reasons.append("negative_available_carbohydrate")

        return CreateFoodImportCommand(
            source_name=FOODDATA_CENTRAL_SOURCE_NAME,
            external_id=fdc_id,
            raw_payload=payload,
            candidate_name=name,
            calories_per_100=nutrients.get("calories"),
            protein_per_100=nutrients.get("protein"),
            carbs_per_100=available_carbs,
            fat_per_100=nutrients.get("fat"),
            review_reasons=tuple(dict.fromkeys(reasons)),
        )


def _nutrients(payload: dict[str, object], reasons: list[str]) -> dict[str, Decimal]:
    raw_nutrients = payload.get("foodNutrients")
    if not isinstance(raw_nutrients, list):
        reasons.extend(f"missing_{name}" for name in _NUTRIENT_IDS)
        return {}
    values: dict[int, Decimal] = {}
    units: dict[int, str | None] = {}
    for item_value in raw_nutrients:
        if not isinstance(item_value, dict):
            continue
        item = cast(dict[str, object], item_value)
        nutrient_value = item.get("nutrient")
        if not isinstance(nutrient_value, dict):
            continue
        nutrient = cast(dict[str, object], nutrient_value)
        nutrient_id = nutrient.get("id")
        if not isinstance(nutrient_id, int):
            continue
        amount = _decimal(item.get("amount"))
        if amount is None or amount < 0:
            continue
        values[nutrient_id] = amount
        units[nutrient_id] = _text(nutrient.get("unitName"))

    result: dict[str, Decimal] = {}
    for name, nutrient_id in _NUTRIENT_IDS.items():
        amount = values.get(nutrient_id)
        if amount is None or (name == "calories" and units.get(nutrient_id) != "kcal"):
            reasons.append(f"missing_{name}")
        else:
            result[name] = amount
    return result


def _decimal(value: object) -> Decimal | None:
    try:
        number = Decimal(str(value))
    except InvalidOperation:
        return None
    return number if number.is_finite() else None


def _text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def fetch_json(url: str, timeout: float) -> dict[str, object]:
    request = Request(url, headers={"User-Agent": "PrepPilot/0.1"})
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = json.load(response)
    except HTTPError as error:
        if error.code == 404:
            raise FoodSourceNotFoundError("FoodData Central food not found") from error
        raise FoodSourceUnavailableError("FoodData Central request failed") from error
    except (URLError, TimeoutError, OSError) as error:
        raise FoodSourceUnavailableError("FoodData Central request failed") from error
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise FoodSourcePayloadError(
            "FoodData Central returned invalid JSON"
        ) from error
    if not isinstance(payload, dict):
        raise FoodSourcePayloadError("unexpected FoodData Central response")
    return cast(dict[str, object], payload)


@lru_cache
def get_fooddata_central_source() -> FoodDataCentralSource:
    settings = get_settings()
    return FoodDataCentralSource(
        api_key=settings.food_data_central_api_key,
        base_url=settings.fooddata_central_base_url,
        timeout_seconds=settings.external_request_timeout_seconds,
        fetch_json=fetch_json,
    )
