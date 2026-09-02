import hashlib
import html as html_module
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Literal, cast
from urllib.request import Request, urlopen

from sqlalchemy import select
from sqlalchemy.orm import Session

from preppilot_api.models import Recipe

NHS_RECIPE_URLS = (
    "https://www.nhs.uk/healthier-families/recipes/roast-dinner/",
    "https://www.nhs.uk/healthier-families/recipes/pasta-carbonara/",
    "https://www.nhs.uk/healthier-families/recipes/roast-chicken-drumsticks/",
    "https://www.nhs.uk/healthier-families/recipes/roast-chicken-breast-with-peppers/",
    "https://www.nhs.uk/healthier-families/recipes/sweet-and-sour-chicken/",
    "https://www.nhs.uk/healthier-families/recipes/brilliant-beef-curry/",
    "https://www.nhs.uk/healthier-families/recipes/classic-cottage-pie/",
    "https://www.nhs.uk/healthier-families/recipes/salmon-and-broccoli-pasta/",
    "https://www.nhs.uk/healthier-families/recipes/super-scrambled-eggs/",
    "https://www.nhs.uk/healthier-families/recipes/sausage-tomato-butter-bean-bake/",
)
SOURCE_NAME = "nhs-healthier-families"
LICENSE_NAME = "Open Government Licence v3.0"
ATTRIBUTION_TEXT = "Information from the NHS website"


@dataclass(frozen=True)
class ParsedRecipe:
    source_url: str
    title: str
    servings: int
    calories: Decimal
    protein: Decimal
    carbs: Decimal
    fat: Decimal
    ingredients: list[str]
    instructions: list[str]
    preparation_minutes: int | None
    cooking_minutes: int | None
    raw_payload: dict[str, object]
    content_hash: str


@dataclass(frozen=True)
class ImportItem:
    source_url: str
    status: Literal["created", "updated", "unchanged", "rejected"]
    title: str | None = None
    reason: str | None = None


def import_nhs_recipes(session: Session) -> tuple[ImportItem, ...]:
    results: list[ImportItem] = []
    for url in NHS_RECIPE_URLS:
        try:
            parsed = parse_recipe_page(url, fetch_recipe_page(url))
            results.append(_store_recipe(session, parsed))
        except (OSError, ValueError, json.JSONDecodeError) as error:
            results.append(ImportItem(url, "rejected", reason=str(error)))
    session.commit()
    return tuple(results)


def fetch_recipe_page(url: str) -> str:
    if url not in NHS_RECIPE_URLS:
        raise ValueError("URL is not in the approved NHS recipe list")
    request = Request(url, headers={"User-Agent": "PrepPilot/0.2 recipe importer"})
    with urlopen(request, timeout=15) as response:
        return cast(str, response.read().decode("utf-8"))


def parse_recipe_page(source_url: str, page: str) -> ParsedRecipe:
    recipe_data = _recipe_json_ld(page)
    visible_text = " ".join(
        html_module.unescape(value).strip()
        for value in re.findall(r">([^<>]+)<", page)
        if value.strip()
    )
    title = _required_string(recipe_data.get("name"), "title")
    ingredients = _string_list(recipe_data.get("recipeIngredient"), "ingredients")
    instructions = _instructions(recipe_data.get("recipeInstructions"))
    servings = int(_required_match(visible_text, r"Serves\s+(\d+)", "servings"))
    calories = _decimal_match(visible_text, r"([\d.]+)\s*kcal", "calories")
    protein = _decimal_match(visible_text, r"([\d.]+)\s*g protein", "protein")
    carbs = _decimal_match(visible_text, r"([\d.]+)\s*g carbohydrate", "carbs")
    fat = _decimal_match(visible_text, r"([\d.]+)\s*g fat", "fat")
    preparation = _optional_minutes(visible_text, "Prep")
    cooking = _optional_minutes(visible_text, "Cook")
    payload: dict[str, object] = {
        "title": title,
        "servings": servings,
        "calories_per_serving": str(calories),
        "protein_per_serving": str(protein),
        "carbs_per_serving": str(carbs),
        "fat_per_serving": str(fat),
        "ingredients": ingredients,
        "instructions": instructions,
        "preparation_minutes": preparation,
        "cooking_minutes": cooking,
    }
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()
    return ParsedRecipe(
        source_url,
        title,
        servings,
        calories,
        protein,
        carbs,
        fat,
        ingredients,
        instructions,
        preparation,
        cooking,
        payload,
        hashlib.sha256(encoded).hexdigest(),
    )


def _store_recipe(session: Session, parsed: ParsedRecipe) -> ImportItem:
    recipe = session.scalar(
        select(Recipe).where(
            Recipe.source_name == SOURCE_NAME,
            Recipe.external_id == parsed.source_url,
        )
    )
    if recipe is not None and recipe.content_hash == parsed.content_hash:
        return ImportItem(parsed.source_url, "unchanged", parsed.title)
    status: Literal["created", "updated"] = "created" if recipe is None else "updated"
    if recipe is None:
        recipe = Recipe(source_name=SOURCE_NAME, external_id=parsed.source_url)
        session.add(recipe)
    recipe.source_url = parsed.source_url
    recipe.title = parsed.title
    recipe.servings = parsed.servings
    recipe.calories_per_serving = parsed.calories
    recipe.protein_per_serving = parsed.protein
    recipe.carbs_per_serving = parsed.carbs
    recipe.fat_per_serving = parsed.fat
    recipe.ingredients = parsed.ingredients
    recipe.instructions = parsed.instructions
    recipe.preparation_minutes = parsed.preparation_minutes
    recipe.cooking_minutes = parsed.cooking_minutes
    recipe.raw_payload = parsed.raw_payload
    recipe.content_hash = parsed.content_hash
    recipe.imported_at = datetime.now(UTC)
    recipe.license_name = LICENSE_NAME
    recipe.attribution_text = ATTRIBUTION_TEXT
    return ImportItem(parsed.source_url, status, parsed.title)


def _recipe_json_ld(page: str) -> dict[str, object]:
    blocks = re.findall(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        page,
        re.DOTALL | re.IGNORECASE,
    )
    for block in blocks:
        candidate = json.loads(html_module.unescape(block))
        if isinstance(candidate, dict) and candidate.get("@type") == "Recipe":
            return candidate
    raise ValueError("recipe JSON-LD missing")


def _required_string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} missing")
    return value.strip()


def _string_list(value: object, field: str) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{field} missing")
    result = [item.strip() for item in value if isinstance(item, str) and item.strip()]
    if not result:
        raise ValueError(f"{field} missing")
    return result


def _instructions(value: object) -> list[str]:
    if isinstance(value, str):
        result = [line.strip() for line in value.splitlines() if line.strip()]
    elif isinstance(value, list):
        result = []
        for item in value:
            if isinstance(item, str) and item.strip():
                result.append(item.strip())
            elif isinstance(item, dict) and isinstance(item.get("text"), str):
                result.extend(
                    line.strip() for line in item["text"].splitlines() if line.strip()
                )
    else:
        result = []
    if not result:
        raise ValueError("instructions missing")
    return result


def _required_match(text: str, pattern: str, field: str) -> str:
    match = re.search(pattern, text, re.IGNORECASE)
    if match is None:
        raise ValueError(f"{field} missing")
    return match.group(1)


def _decimal_match(text: str, pattern: str, field: str) -> Decimal:
    return Decimal(_required_match(text, pattern, field))


def _optional_minutes(text: str, label: str) -> int | None:
    match = re.search(rf"{label}:\s*(\d+)\s*mins?", text, re.IGNORECASE)
    return int(match.group(1)) if match else None
