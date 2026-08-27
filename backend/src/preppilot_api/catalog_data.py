import json
from dataclasses import dataclass
from decimal import Decimal
from importlib.resources import files

from pydantic import BaseModel, ConfigDict, Field, model_validator

from preppilot_api.food_resolution import (
    CatalogFoodDefinition,
    CatalogPortionDefinition,
)
from preppilot_api.ingredient_names import normalize_ingredient_name
from preppilot_api.models import MeasurementUnit


class _CatalogModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class _FoodDefinition(_CatalogModel):
    name: str
    unit: MeasurementUnit
    calories_per_100: Decimal
    protein_per_100: Decimal
    carbs_per_100: Decimal
    fat_per_100: Decimal
    source_name: str
    source_reference: str


class _PortionDefinition(_CatalogModel):
    amount: Decimal
    unit: str
    modifier: str | None = None
    gram_weight: Decimal
    source_name: str
    source_reference: str | None = None


class _ResolutionEntry(_CatalogModel):
    source_name: str
    external_name: str
    preferred_fdc_id: int | None = None
    food: _FoodDefinition | None = None
    portions: list[_PortionDefinition] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_resolution_choice(self) -> "_ResolutionEntry":
        if self.preferred_fdc_id is not None and self.food is not None:
            raise ValueError("An entry cannot define both preferred_fdc_id and food")
        return self


class _CatalogFile(_CatalogModel):
    resolutions: list[_ResolutionEntry]


@dataclass(frozen=True)
class CatalogConfiguration:
    preferred_fdc_ids: dict[tuple[str, str], int]
    foods: dict[tuple[str, str], CatalogFoodDefinition]
    portions: dict[tuple[str, str], tuple[CatalogPortionDefinition, ...]]


def load_catalog_configuration() -> CatalogConfiguration:
    resource = files("preppilot_api").joinpath("catalog_overrides.json")
    parsed = _CatalogFile.model_validate(
        json.loads(resource.read_text(encoding="utf-8"))
    )

    preferred_fdc_ids: dict[tuple[str, str], int] = {}
    foods: dict[tuple[str, str], CatalogFoodDefinition] = {}
    portions: dict[tuple[str, str], tuple[CatalogPortionDefinition, ...]] = {}
    for entry in parsed.resolutions:
        key = (
            entry.source_name.strip().casefold(),
            normalize_ingredient_name(entry.external_name),
        )
        if key in preferred_fdc_ids or key in foods or key in portions:
            raise ValueError(f"Duplicate catalog resolution for {key!r}")
        if entry.preferred_fdc_id is not None:
            preferred_fdc_ids[key] = entry.preferred_fdc_id
        if entry.food is not None:
            foods[key] = CatalogFoodDefinition(**entry.food.model_dump())
        if entry.portions:
            portions[key] = tuple(
                CatalogPortionDefinition(**portion.model_dump())
                for portion in entry.portions
            )

    return CatalogConfiguration(preferred_fdc_ids, foods, portions)
