import json
import re
import unicodedata
from decimal import Decimal
from importlib.resources import files

from pydantic import BaseModel, ConfigDict, Field, model_validator

from preppilot_api.models import MealRole, MeasurementUnit


class CatalogModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class FoodMeasureDefaultDefinition(CatalogModel):
    key: str = Field(min_length=1)
    amount: Decimal = Field(gt=0)
    source_name: str = Field(min_length=1)
    source_reference: str | None = None


class FoodDefinition(CatalogModel):
    key: str = Field(pattern=r"^[a-z0-9_]+$")
    name: str = Field(min_length=1)
    brand: str | None = None
    unit: MeasurementUnit
    calories_per_100: Decimal = Field(ge=0)
    protein_per_100: Decimal = Field(ge=0)
    carbs_per_100: Decimal = Field(ge=0)
    fat_per_100: Decimal = Field(ge=0)
    source_name: str = Field(min_length=1)
    source_reference: str | None = None
    aliases: tuple[str, ...] = ()
    measure_defaults: tuple[FoodMeasureDefaultDefinition, ...] = ()

    @model_validator(mode="after")
    def validate_normalization_metadata(self) -> "FoodDefinition":
        normalized_aliases = [_normalization_key(alias) for alias in self.aliases]
        if any(not alias for alias in normalized_aliases):
            raise ValueError(f"Food {self.key!r} contains a blank alias")
        if len(set(normalized_aliases)) != len(normalized_aliases):
            raise ValueError(f"Food {self.key!r} contains duplicate aliases")
        measure_keys = [
            _normalization_key(default.key) for default in self.measure_defaults
        ]
        if len(set(measure_keys)) != len(measure_keys):
            raise ValueError(f"Food {self.key!r} contains duplicate measure defaults")
        return self


class MealIngredientDefinition(CatalogModel):
    food_key: str = Field(pattern=r"^[a-z0-9_]+$")
    amount: Decimal = Field(gt=0)


class MealDefinition(CatalogModel):
    key: str = Field(pattern=r"^[a-z0-9_]+$")
    name: str = Field(min_length=1)
    preparation_minutes: int = Field(ge=0)
    instructions: str = Field(min_length=1)
    roles: tuple[MealRole, ...] = Field(min_length=1)
    portion_factors: tuple[Decimal, ...] = Field(min_length=1)
    ingredients: tuple[MealIngredientDefinition, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_unique_assignments(self) -> "MealDefinition":
        if len(set(self.roles)) != len(self.roles):
            raise ValueError(f"Meal {self.key!r} contains duplicate roles")
        allowed_factors = {Decimal("0.5"), Decimal("1"), Decimal("1.5"), Decimal("2")}
        if any(factor not in allowed_factors for factor in self.portion_factors):
            raise ValueError(
                f"Meal {self.key!r} contains an unsupported portion factor"
            )
        if tuple(sorted(set(self.portion_factors))) != self.portion_factors:
            raise ValueError(
                f"Meal {self.key!r} portion factors must be unique and sorted"
            )
        food_keys = [ingredient.food_key for ingredient in self.ingredients]
        if len(set(food_keys)) != len(food_keys):
            raise ValueError(f"Meal {self.key!r} contains duplicate ingredients")
        return self


class Catalog(CatalogModel):
    foods: tuple[FoodDefinition, ...] = Field(min_length=1)
    meals: tuple[MealDefinition, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_catalog(self) -> "Catalog":
        food_keys = [food.key for food in self.foods]
        if len(set(food_keys)) != len(food_keys):
            raise ValueError("Catalog contains duplicate food keys")

        alias_owners: dict[str, str] = {}
        food_identity_owners = {
            identity: food.key
            for food in self.foods
            for identity in (
                _normalization_key(food.key),
                _normalization_key(food.name),
            )
        }
        for food in self.foods:
            for alias in food.aliases:
                normalized_alias = _normalization_key(alias)
                owner = alias_owners.setdefault(normalized_alias, food.key)
                if owner != food.key:
                    raise ValueError(
                        f"Alias {alias!r} belongs to both {owner!r} and {food.key!r}"
                    )
                identity_owner = food_identity_owners.get(normalized_alias)
                if identity_owner is not None and identity_owner != food.key:
                    raise ValueError(
                        f"Alias {alias!r} conflicts with food {identity_owner!r}"
                    )

        meal_keys = [meal.key for meal in self.meals]
        if len(set(meal_keys)) != len(meal_keys):
            raise ValueError("Catalog contains duplicate meal keys")

        known_foods = set(food_keys)
        missing_foods = {
            ingredient.food_key
            for meal in self.meals
            for ingredient in meal.ingredients
            if ingredient.food_key not in known_foods
        }
        if missing_foods:
            raise ValueError(
                f"Meals reference unknown foods: {', '.join(sorted(missing_foods))}"
            )
        return self


def load_catalog() -> Catalog:
    resource = files("preppilot_api").joinpath("catalog.json")
    return Catalog.model_validate_json(resource.read_text(encoding="utf-8"))


def parse_catalog(value: str) -> Catalog:
    return Catalog.model_validate(json.loads(value))


def _normalization_key(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return " ".join(re.sub(r"[^\w]+", " ", normalized).split())
