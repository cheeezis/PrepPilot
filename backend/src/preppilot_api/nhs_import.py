import hashlib
import html as html_module
import json
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from html.parser import HTMLParser
from typing import Literal, cast
from urllib.parse import urlencode, urljoin, urlsplit
from urllib.request import Request, urlopen

from sqlalchemy import select
from sqlalchemy.orm import Session

from preppilot_api.models import Recipe

RecipeCategory = Literal["breakfast", "lunch", "dinner", "snack"]

NHS_ORIGIN = "https://www.nhs.uk"
NHS_RECIPE_SEARCH_URL = f"{NHS_ORIGIN}/healthier-families/recipe_search/"
NHS_SOURCE_FILTERS: tuple[tuple[str, RecipeCategory], ...] = (
    ("Breakfast", "breakfast"),
    ("Lunch", "lunch"),
    ("Dinner", "dinner"),
    ("Snacks", "snack"),
    ("Drinks", "snack"),
)
NHS_EXCLUDED_FILTER = "Puddings"
NHS_RECIPE_PATH = re.compile(r"^/healthier-families/recipes/[a-z0-9-]+/$")
SOURCE_NAME = "nhs-healthier-families"
LICENSE_NAME = "Open Government Licence v3.0"
ATTRIBUTION_TEXT = "Information from the NHS website"


@dataclass(frozen=True)
class ParsedRecipe:
    source_url: str
    title: str
    categories: tuple[RecipeCategory, ...]
    servings: int
    calories: Decimal
    protein: Decimal
    carbs: Decimal
    fat: Decimal
    sugar: Decimal | None
    saturated_fat: Decimal | None
    fiber: Decimal | None
    salt: Decimal | None
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
    discovered = discover_nhs_recipe_categories()
    with ThreadPoolExecutor(max_workers=4) as executor:
        candidates = executor.map(_fetch_candidate, discovered)
        for candidate in candidates:
            if isinstance(candidate, ImportItem):
                results.append(candidate)
            else:
                parsed = candidate
                results.append(_store_recipe(session, parsed))
    session.commit()
    return tuple(results)


def discover_nhs_recipe_categories(
) -> tuple[tuple[str, tuple[RecipeCategory, ...]], ...]:
    categories_by_url: dict[str, set[RecipeCategory]] = {}
    with ThreadPoolExecutor(max_workers=4) as executor:
        source_pages = executor.map(
            fetch_recipe_index,
            [source_filter for source_filter, _ in NHS_SOURCE_FILTERS],
        )
        for (_, category), page in zip(NHS_SOURCE_FILTERS, source_pages, strict=True):
            for url in _recipe_links(page):
                categories_by_url.setdefault(url, set()).add(category)

    excluded_urls = set(_recipe_links(fetch_recipe_index(NHS_EXCLUDED_FILTER)))
    category_order: tuple[RecipeCategory, ...] = (
        "breakfast",
        "lunch",
        "dinner",
        "snack",
    )
    return tuple(
        (
            url,
            tuple(category for category in category_order if category in categories),
        )
        for url, categories in sorted(categories_by_url.items())
        if url not in excluded_urls
    )


def fetch_recipe_index(source_filter: str) -> str:
    query = urlencode((("Meal", "OR"), ("Meal", source_filter)))
    request = Request(
        f"{NHS_RECIPE_SEARCH_URL}?{query}",
        headers={"User-Agent": "PrepPilot/0.3 recipe importer"},
    )
    with urlopen(request, timeout=15) as response:
        return cast(str, response.read().decode("utf-8"))


def _recipe_links(page: str) -> tuple[str, ...]:
    paths = re.findall(
        r'href=["\'](/healthier-families/recipes/[a-z0-9-]+/)["\']',
        page,
        re.IGNORECASE,
    )
    return tuple(sorted({urljoin(NHS_ORIGIN, path) for path in paths}))


def _fetch_candidate(
    candidate: tuple[str, tuple[RecipeCategory, ...]],
) -> ParsedRecipe | ImportItem:
    url, categories = candidate
    try:
        return parse_recipe_page(url, fetch_recipe_page(url), categories)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        return ImportItem(url, "rejected", reason=str(error))


def fetch_recipe_page(url: str) -> str:
    parsed_url = urlsplit(url)
    if (
        parsed_url.scheme != "https"
        or parsed_url.netloc != "www.nhs.uk"
        or not NHS_RECIPE_PATH.fullmatch(parsed_url.path)
        or parsed_url.query
        or parsed_url.fragment
    ):
        raise ValueError("URL is not an approved NHS recipe URL")
    request = Request(url, headers={"User-Agent": "PrepPilot/0.3 recipe importer"})
    with urlopen(request, timeout=15) as response:
        return cast(str, response.read().decode("utf-8"))


def parse_recipe_page(
    source_url: str,
    page: str,
    categories: tuple[RecipeCategory, ...] = ("dinner",),
) -> ParsedRecipe:
    recipe_data = _recipe_json_ld(page)
    visible_text = " ".join(
        html_module.unescape(value).strip()
        for value in re.findall(r">([^<>]+)<", page)
        if value.strip()
    )
    title = _required_string(recipe_data.get("name"), "title")
    ingredients = _string_list(recipe_data.get("recipeIngredient"), "ingredients")
    instructions = _method_instructions(page) or _instructions(
        recipe_data.get("recipeInstructions")
    )
    servings = int(_required_match(visible_text, r"Serves\s+(\d+)", "servings"))
    calories = _decimal_match(visible_text, r"([\d.]+)\s*kcal", "calories")
    protein = _decimal_match(visible_text, r"([\d.]+)\s*g protein", "protein")
    carbs = _decimal_match(visible_text, r"([\d.]+)\s*g carbohydrate", "carbs")
    fat = _decimal_match(visible_text, r"([\d.]+)\s*g fat", "fat")
    sugar = _optional_decimal_match(
        visible_text,
        r"carbohydrate,?\s+of which\s+([\d.]+)\s*g sugars",
    )
    saturated_fat = _optional_decimal_match(
        visible_text,
        r"fat,?\s+of which\s+([\d.]+)\s*g saturates",
    )
    fiber = _optional_decimal_match(visible_text, r"([\d.]+)\s*g fibre")
    salt = _optional_decimal_match(visible_text, r"([\d.]+)\s*g salt")
    _validate_nutrients(calories, protein, carbs, fat)
    preparation = _optional_minutes(visible_text, "Prep")
    cooking = _optional_minutes(visible_text, "Cook")
    payload: dict[str, object] = {
        "title": title,
        "categories": categories,
        "servings": servings,
        "calories_per_serving": str(calories),
        "protein_per_serving": str(protein),
        "carbs_per_serving": str(carbs),
        "fat_per_serving": str(fat),
        "sugar_per_serving": _optional_decimal_string(sugar),
        "saturated_fat_per_serving": _optional_decimal_string(saturated_fat),
        "fiber_per_serving": _optional_decimal_string(fiber),
        "salt_per_serving": _optional_decimal_string(salt),
        "ingredients": ingredients,
        "instructions": instructions,
        "preparation_minutes": preparation,
        "cooking_minutes": cooking,
    }
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()
    return ParsedRecipe(
        source_url=source_url,
        title=title,
        categories=categories,
        servings=servings,
        calories=calories,
        protein=protein,
        carbs=carbs,
        fat=fat,
        sugar=sugar,
        saturated_fat=saturated_fat,
        fiber=fiber,
        salt=salt,
        ingredients=ingredients,
        instructions=instructions,
        preparation_minutes=preparation,
        cooking_minutes=cooking,
        raw_payload=payload,
        content_hash=hashlib.sha256(encoded).hexdigest(),
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
    recipe.categories = list(parsed.categories)
    recipe.servings = parsed.servings
    recipe.calories_per_serving = parsed.calories
    recipe.protein_per_serving = parsed.protein
    recipe.carbs_per_serving = parsed.carbs
    recipe.fat_per_serving = parsed.fat
    recipe.sugar_per_serving = parsed.sugar
    recipe.saturated_fat_per_serving = parsed.saturated_fat
    recipe.fiber_per_serving = parsed.fiber
    recipe.salt_per_serving = parsed.salt
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
    result = _instruction_items(value)
    if not result:
        raise ValueError("instructions missing")
    return result


def _method_instructions(page: str) -> list[str]:
    parser = _MethodListParser()
    parser.feed(page)
    parser.close()
    return parser.steps


class _MethodListParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.method_nesting = 0
        self.list_nesting = 0
        self.step_nesting = 0
        self.step_parts: list[str] = []
        self.steps: list[str] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        classes = dict(attrs).get("class", "") or ""
        if tag == "div":
            if self.method_nesting:
                self.method_nesting += 1
            elif "bh-recipe-instructions__method" in classes.split():
                self.method_nesting = 1
        if tag == "ol" and self.method_nesting:
            self.list_nesting += 1
        if tag == "li" and self.list_nesting:
            if not self.step_nesting:
                self.step_parts = []
            self.step_nesting += 1

    def handle_startendtag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        if tag == "li" and self.step_nesting:
            self.step_nesting -= 1
            if not self.step_nesting:
                step = re.sub(r"\s+", " ", " ".join(self.step_parts)).strip()
                if step:
                    self.steps.append(step)
                self.step_parts = []
        if tag == "ol" and self.list_nesting:
            self.list_nesting -= 1
        if tag == "div" and self.method_nesting:
            self.method_nesting -= 1

    def handle_data(self, data: str) -> None:
        if self.step_nesting and data.strip():
            self.step_parts.append(data.strip())


def _instruction_items(value: object) -> list[str]:
    if isinstance(value, str):
        return _split_instruction_text(value)
    if isinstance(value, list):
        return [step for item in value for step in _instruction_items(item)]
    if not isinstance(value, dict):
        return []

    nested = value.get("itemListElement")
    if nested is not None:
        nested_steps = _instruction_items(nested)
        if nested_steps:
            return nested_steps

    text = value.get("text")
    return _split_instruction_text(text) if isinstance(text, str) else []


def _split_instruction_text(value: str) -> list[str]:
    text = html_module.unescape(value).replace("\u00a0", " ").strip()
    if not text:
        return []

    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    result: list[str] = []
    for line in (line for line in lines if line):
        markers = list(re.finditer(r"(?i)(?<!\w)(?:step\s+)?\d+[.)]\s+", line))
        if len(markers) < 2 or markers[0].start() != 0:
            result.append(_without_step_marker(line))
            continue
        for index, marker in enumerate(markers):
            end = markers[index + 1].start() if index + 1 < len(markers) else len(line)
            step = line[marker.end():end].strip()
            if step:
                result.append(step)
    return result


def _without_step_marker(value: str) -> str:
    return re.sub(r"(?i)^(?:step\s+)?\d+[.)]\s+", "", value).strip()


def _required_match(text: str, pattern: str, field: str) -> str:
    match = re.search(pattern, text, re.IGNORECASE)
    if match is None:
        raise ValueError(f"{field} missing")
    return match.group(1)


def _decimal_match(text: str, pattern: str, field: str) -> Decimal:
    return Decimal(_required_match(text, pattern, field))


def _optional_decimal_match(text: str, pattern: str) -> Decimal | None:
    match = re.search(pattern, text, re.IGNORECASE)
    return None if match is None else Decimal(match.group(1))


def _optional_decimal_string(value: Decimal | None) -> str | None:
    return None if value is None else str(value)


def _optional_minutes(text: str, label: str) -> int | None:
    match = re.search(rf"{label}:\s*(\d+)\s*mins?", text, re.IGNORECASE)
    return int(match.group(1)) if match else None


def _validate_nutrients(
    calories: Decimal, protein: Decimal, carbs: Decimal, fat: Decimal
) -> None:
    if calories <= 0 or min(protein, carbs, fat) < 0:
        raise ValueError("nutrient values invalid")
    macro_calories = protein * 4 + carbs * 4 + fat * 9
    if macro_calories > calories * Decimal("1.25"):
        raise ValueError("nutrient energy inconsistent")
