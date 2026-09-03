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
from urllib.request import Request, urlopen

from sqlalchemy import select
from sqlalchemy.orm import Session

from preppilot_api.models import Recipe

RecipeCategory = Literal["breakfast", "lunch", "dinner"]

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
    "https://www.nhs.uk/healthier-families/recipes/bajan-cou-cou-with-spicy-fish/",
    "https://www.nhs.uk/healthier-families/recipes/baked-potatoes-with-mince/",
    "https://www.nhs.uk/healthier-families/recipes/bengali-chicken-curry/",
    "https://www.nhs.uk/healthier-families/recipes/caribbean-tofu-and-sweet-potato-curry-with-rice-and-peas/",
    "https://www.nhs.uk/healthier-families/recipes/chilli-con-carne/",
    "https://www.nhs.uk/healthier-families/recipes/homemade-fish-fingers-with-sweet-potato-wedges/",
    "https://www.nhs.uk/healthier-families/recipes/falafels/",
    "https://www.nhs.uk/healthier-families/recipes/healthier-full-english-breakfast/",
    "https://www.nhs.uk/healthier-families/recipes/meat-free-cottage-pie/",
    "https://www.nhs.uk/healthier-families/recipes/prawn-jambalaya/",
)
NHS_RECIPE_CATEGORIES: dict[str, RecipeCategory] = {
    "https://www.nhs.uk/healthier-families/recipes/super-scrambled-eggs/": "breakfast",
    "https://www.nhs.uk/healthier-families/recipes/falafels/": "lunch",
    "https://www.nhs.uk/healthier-families/recipes/healthier-full-english-breakfast/": "breakfast",
}
SOURCE_NAME = "nhs-healthier-families"
LICENSE_NAME = "Open Government Licence v3.0"
ATTRIBUTION_TEXT = "Information from the NHS website"


@dataclass(frozen=True)
class ParsedRecipe:
    source_url: str
    title: str
    category: RecipeCategory
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
    with ThreadPoolExecutor(max_workers=4) as executor:
        candidates = executor.map(_fetch_candidate, NHS_RECIPE_URLS)
        for candidate in candidates:
            if isinstance(candidate, ImportItem):
                results.append(candidate)
            else:
                parsed = candidate
                results.append(_store_recipe(session, parsed))
    session.commit()
    return tuple(results)


def _fetch_candidate(url: str) -> ParsedRecipe | ImportItem:
    try:
        return parse_recipe_page(url, fetch_recipe_page(url))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        return ImportItem(url, "rejected", reason=str(error))


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
    category = NHS_RECIPE_CATEGORIES.get(source_url, "dinner")
    ingredients = _string_list(recipe_data.get("recipeIngredient"), "ingredients")
    instructions = _method_instructions(page) or _instructions(
        recipe_data.get("recipeInstructions")
    )
    servings = int(_required_match(visible_text, r"Serves\s+(\d+)", "servings"))
    calories = _decimal_match(visible_text, r"([\d.]+)\s*kcal", "calories")
    protein = _decimal_match(visible_text, r"([\d.]+)\s*g protein", "protein")
    carbs = _decimal_match(visible_text, r"([\d.]+)\s*g carbohydrate", "carbs")
    fat = _decimal_match(visible_text, r"([\d.]+)\s*g fat", "fat")
    _validate_nutrients(calories, protein, carbs, fat)
    preparation = _optional_minutes(visible_text, "Prep")
    cooking = _optional_minutes(visible_text, "Cook")
    payload: dict[str, object] = {
        "title": title,
        "category": category,
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
        source_url=source_url,
        title=title,
        category=category,
        servings=servings,
        calories=calories,
        protein=protein,
        carbs=carbs,
        fat=fat,
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
    recipe.category = parsed.category
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
