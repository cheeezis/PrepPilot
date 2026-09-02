import argparse
import json
import re
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Protocol, cast
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from sqlalchemy.orm import Session

from preppilot_api.database import engine
from preppilot_api.recipe_imports import (
    CreateRecipeImportCommand,
    ExternalIngredientIdentityPayload,
    ExternalIngredientPayload,
    ExternalRecipePayload,
    create_recipe_import,
)

API_URL = "https://en.wikibooks.org/w/api.php"
SOURCE_NAME = "wikibooks"
LICENSE_NAME = "CC BY-SA 4.0"
LICENSE_URL = "https://creativecommons.org/licenses/by-sa/4.0/"


@dataclass(frozen=True)
class WikibooksPage:
    page_id: int
    title: str
    revision_id: int
    revision_timestamp: str
    url: str
    wikitext: str


@dataclass(frozen=True)
class ParsedIngredient:
    line: str
    name: str
    amount: str | None
    unit: str | None
    source_title: str | None


@dataclass(frozen=True)
class ParsedRecipe:
    title: str
    servings: str
    instructions: str
    ingredients: tuple[ParsedIngredient, ...]


@dataclass(frozen=True)
class ImportCandidateResult:
    page_id: int
    title: str
    status: str
    reasons: tuple[str, ...]
    ingredient_count: int


@dataclass(frozen=True)
class WikibooksImportReport:
    discovered: int
    eligible: int
    rejected: int
    imported: int
    duplicates: int
    write_enabled: bool
    candidates: tuple[ImportCandidateResult, ...]


class WikibooksSource(Protocol):
    def fetch_recipe_pages(self, limit: int) -> tuple[WikibooksPage, ...]: ...

    def resolve_page_ids(self, titles: set[str]) -> dict[str, int]: ...


class MediaWikiClient:
    def fetch_recipe_pages(self, limit: int) -> tuple[WikibooksPage, ...]:
        payload = self._request(
            {
                "action": "query",
                "generator": "categorymembers",
                "gcmtitle": "Category:Recipes",
                "gcmnamespace": "102",
                "gcmlimit": str(limit),
                "gcmsort": "sortkey",
                "gcmdir": "ascending",
                "prop": "revisions|info",
                "rvprop": "ids|timestamp|content",
                "rvslots": "main",
                "inprop": "url",
                "format": "json",
                "formatversion": "2",
            }
        )
        query = _mapping(payload.get("query"))
        pages = _sequence(query.get("pages"))
        return tuple(_page_from_api(page) for page in pages)

    def resolve_page_ids(self, titles: set[str]) -> dict[str, int]:
        resolved: dict[str, int] = {}
        ordered_titles = sorted(titles)
        for start in range(0, len(ordered_titles), 50):
            batch = ordered_titles[start : start + 50]
            payload = self._request(
                {
                    "action": "query",
                    "titles": "|".join(batch),
                    "prop": "info",
                    "format": "json",
                    "formatversion": "2",
                }
            )
            query = _mapping(payload.get("query"))
            for page_value in _sequence(query.get("pages")):
                page = _mapping(page_value)
                if "missing" in page:
                    continue
                title = _text(page.get("title"), "page title")
                resolved[_title_key(title)] = _integer(page.get("pageid"), "page ID")
        return resolved

    def _request(self, parameters: dict[str, str]) -> dict[str, object]:
        request = Request(
            f"{API_URL}?{urlencode(parameters)}",
            headers={"User-Agent": "PrepPilot/0.1 (local development)"},
        )
        with urlopen(request, timeout=20) as response:  # noqa: S310
            payload: object = json.loads(response.read().decode("utf-8"))
        return _mapping(payload)


def run_wikibooks_import(
    source: WikibooksSource,
    *,
    limit: int,
    session: Session | None = None,
    write: bool = False,
) -> WikibooksImportReport:
    if limit < 1 or limit > 25:
        raise ValueError("limit must be between 1 and 25")
    if write and session is None:
        raise ValueError("a database session is required when write is enabled")

    pages = source.fetch_recipe_pages(limit)
    parsed_pages: list[tuple[WikibooksPage, ParsedRecipe]] = []
    results: list[ImportCandidateResult] = []
    source_titles: set[str] = set()
    for page in pages:
        parsed, reasons = parse_recipe_page(page)
        if parsed is None:
            results.append(
                ImportCandidateResult(
                    page_id=page.page_id,
                    title=page.title,
                    status="rejected",
                    reasons=reasons,
                    ingredient_count=_ingredient_line_count(page.wikitext),
                )
            )
            continue
        parsed_pages.append((page, parsed))
        source_titles.update(
            ingredient.source_title
            for ingredient in parsed.ingredients
            if ingredient.source_title is not None
        )

    source_page_ids = source.resolve_page_ids(source_titles)
    imported = 0
    duplicates = 0
    for page, parsed in parsed_pages:
        missing_links = tuple(
            sorted(
                {
                    ingredient.source_title
                    for ingredient in parsed.ingredients
                    if ingredient.source_title is not None
                    and _title_key(ingredient.source_title) not in source_page_ids
                }
            )
        )
        if missing_links:
            results.append(
                ImportCandidateResult(
                    page_id=page.page_id,
                    title=page.title,
                    status="rejected",
                    reasons=("unresolved_ingredient_link",),
                    ingredient_count=len(parsed.ingredients),
                )
            )
            continue

        status = "eligible"
        if write:
            assert session is not None
            _, created = create_recipe_import(
                session,
                _import_command(page, parsed, source_page_ids),
                source_payload=_source_payload(page),
            )
            if created:
                imported += 1
                status = "imported"
            else:
                duplicates += 1
                status = "duplicate"
        results.append(
            ImportCandidateResult(
                page_id=page.page_id,
                title=page.title,
                status=status,
                reasons=(),
                ingredient_count=len(parsed.ingredients),
            )
        )

    results.sort(key=lambda result: result.page_id)
    eligible = sum(result.status != "rejected" for result in results)
    return WikibooksImportReport(
        discovered=len(pages),
        eligible=eligible,
        rejected=len(pages) - eligible,
        imported=imported,
        duplicates=duplicates,
        write_enabled=write,
        candidates=tuple(results),
    )


def parse_recipe_page(
    page: WikibooksPage,
) -> tuple[ParsedRecipe | None, tuple[str, ...]]:
    reasons: list[str] = []
    servings = _servings(page.wikitext)
    if servings is None:
        reasons.append("missing_or_invalid_servings")

    ingredient_section = _section(page.wikitext, ("ingredients",))
    ingredient_lines = (
        tuple(
            line.strip()[1:].strip()
            for line in ingredient_section.splitlines()
            if line.strip().startswith("*")
        )
        if ingredient_section is not None
        else ()
    )
    ingredients = tuple(
        ingredient
        for line in ingredient_lines
        if (ingredient := _parse_ingredient(line)) is not None
    )
    if not ingredients:
        reasons.append("missing_ingredients")
    elif any(ingredient.source_title is None for ingredient in ingredients):
        reasons.append("ingredient_without_canonical_link")

    procedure = _section(
        page.wikitext,
        ("procedure", "procedure brief", "directions", "method"),
    )
    steps = (
        tuple(
            _plain_text(line.lstrip("#").strip())
            for line in procedure.splitlines()
            if line.strip().startswith("#")
        )
        if procedure is not None
        else ()
    )
    instructions = "\n".join(step for step in steps if step)
    if not instructions:
        reasons.append("missing_procedure")

    if reasons or servings is None:
        return None, tuple(reasons)
    return (
        ParsedRecipe(
            title=page.title.removeprefix("Cookbook:").strip(),
            servings=servings,
            instructions=instructions,
            ingredients=ingredients,
        ),
        (),
    )


def _import_command(
    page: WikibooksPage,
    parsed: ParsedRecipe,
    source_page_ids: dict[str, int],
) -> CreateRecipeImportCommand:
    return CreateRecipeImportCommand(
        source_name=SOURCE_NAME,
        external_id=str(page.page_id),
        fetched_at=datetime.now(UTC),
        payload=ExternalRecipePayload(
            title=parsed.title,
            servings=parsed.servings,
            instructions=parsed.instructions,
            ingredients=tuple(
                ExternalIngredientPayload(
                    line=ingredient.line,
                    name=ingredient.name,
                    amount=ingredient.amount,
                    unit=ingredient.unit,
                    identity=(
                        ExternalIngredientIdentityPayload(
                            source_name=SOURCE_NAME,
                            external_id=str(
                                source_page_ids[_title_key(ingredient.source_title)]
                            ),
                            source_label=ingredient.source_title,
                            source_url=_page_url(ingredient.source_title),
                        )
                        if ingredient.source_title is not None
                        else None
                    ),
                )
                for ingredient in parsed.ingredients
            ),
        ),
    )


def _source_payload(page: WikibooksPage) -> dict[str, object]:
    return {
        "title": page.title.removeprefix("Cookbook:").strip(),
        "source": {
            "name": SOURCE_NAME,
            "page_id": page.page_id,
            "page_title": page.title,
            "revision_id": page.revision_id,
            "revision_timestamp": page.revision_timestamp,
            "page_url": page.url,
            "revision_url": f"{page.url}?oldid={page.revision_id}",
            "license": LICENSE_NAME,
            "license_url": LICENSE_URL,
            "attribution": f"Wikibooks contributors, {page.title}",
        },
        "wikitext": page.wikitext,
    }


def _page_from_api(value: object) -> WikibooksPage:
    page = _mapping(value)
    revisions = _sequence(page.get("revisions"))
    if not revisions:
        raise ValueError("Wikibooks page has no revision")
    revision = _mapping(revisions[0])
    slots = _mapping(revision.get("slots"))
    main_slot = _mapping(slots.get("main"))
    return WikibooksPage(
        page_id=_integer(page.get("pageid"), "page ID"),
        title=_text(page.get("title"), "page title"),
        revision_id=_integer(revision.get("revid"), "revision ID"),
        revision_timestamp=_text(revision.get("timestamp"), "revision timestamp"),
        url=_text(page.get("fullurl"), "page URL"),
        wikitext=_text(main_slot.get("content"), "wikitext"),
    )


def _servings(wikitext: str) -> str | None:
    summary = re.search(
        r"\{\{\s*recipe\s*summary\b(?P<body>.*?)\}\}",
        wikitext,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if summary is None:
        return None
    match = re.search(
        r"(?:^|\|)\s*servings\s*=\s*(?P<value>[^|}\n]+)",
        summary.group("body"),
        flags=re.IGNORECASE,
    )
    if match is None:
        return None
    value = match.group("value").strip()
    try:
        number = Decimal(value)
    except InvalidOperation:
        return None
    return value if number.is_finite() and number > 0 else None


def _section(wikitext: str, names: tuple[str, ...]) -> str | None:
    headings = tuple(
        re.finditer(r"^==\s*(?P<name>[^=]+?)\s*==\s*$", wikitext, re.MULTILINE)
    )
    normalized_names = {name.casefold() for name in names}
    for index, heading in enumerate(headings):
        name = " ".join(heading.group("name").casefold().split())
        name = re.sub(r"\s*\([^)]*\)\s*$", "", name)
        if name not in normalized_names:
            continue
        end = headings[index + 1].start() if index + 1 < len(headings) else len(wikitext)
        return wikitext[heading.end() : end]
    return None


def _ingredient_line_count(wikitext: str) -> int:
    ingredient_section = _section(wikitext, ("ingredients",))
    if ingredient_section is None:
        return 0
    return sum(line.strip().startswith("*") for line in ingredient_section.splitlines())


def _parse_ingredient(line: str) -> ParsedIngredient | None:
    plain = _plain_text(line)
    if not plain:
        return None
    links = tuple(
        re.finditer(
            r"\[\[(?P<title>Cookbook:[^\]|#]+)(?:#[^\]|]*)?(?:\|(?P<label>[^\]]+))?\]\]",
            line,
            flags=re.IGNORECASE,
        )
    )
    food_link = next(
        (
            link
            for link in reversed(links)
            if _title_key(link.group("title")) not in _NON_FOOD_LINKS
        ),
        None,
    )
    source_title = food_link.group("title").strip() if food_link is not None else None
    name = (
        _plain_text(food_link.group("label") or source_title.removeprefix("Cookbook:"))
        if food_link is not None and source_title is not None
        else _ingredient_name_from_plain(plain)
    )
    if not name:
        return None
    amount, unit = _amount_and_unit(plain, name)
    return ParsedIngredient(
        line=plain,
        name=name,
        amount=amount,
        unit=unit,
        source_title=source_title,
    )


def _amount_and_unit(line: str, ingredient_name: str) -> tuple[str | None, str | None]:
    match = re.match(
        r"^(?P<amount>(?:\d+\s+)?[¼½¾⅓⅔⅛⅜⅝⅞]|\d+(?:[.,]\d+)?)"
        r"(?:\s+(?P<unit>[A-Za-z]+))?\b",
        line,
    )
    if match is None:
        return None, None
    amount = _decimal_fraction(match.group("amount"))
    unit = match.group("unit")
    if unit is None:
        return amount, None
    if unit.casefold().rstrip("s") == ingredient_name.casefold().rstrip("s"):
        return amount, "piece"
    return amount, unit


def _decimal_fraction(value: str) -> str:
    fractions = {
        "¼": Decimal("0.25"),
        "½": Decimal("0.5"),
        "¾": Decimal("0.75"),
        "⅓": Decimal("0.333"),
        "⅔": Decimal("0.667"),
        "⅛": Decimal("0.125"),
        "⅜": Decimal("0.375"),
        "⅝": Decimal("0.625"),
        "⅞": Decimal("0.875"),
    }
    for symbol, fraction in fractions.items():
        if symbol in value:
            whole = value.replace(symbol, "").strip()
            return str((Decimal(whole) if whole else Decimal(0)) + fraction)
    return value.replace(",", ".")


def _plain_text(value: str) -> str:
    value = re.sub(r"<ref\b[^>]*>.*?</ref>", "", value, flags=re.I | re.S)
    value = re.sub(r"\{\{.*?\}\}", "", value)
    value = re.sub(
        r"\[\[[^\]|]+\|([^\]]+)\]\]",
        lambda match: cast(str, match.group(1)),
        value,
    )
    value = re.sub(r"\[\[([^\]]+)\]\]", lambda match: cast(str, match.group(1)), value)
    value = re.sub(r"'{2,}", "", value)
    value = re.sub(r"<[^>]+>", "", value)
    return " ".join(value.split())


def _ingredient_name_from_plain(value: str) -> str:
    return re.sub(
        r"^(?:\d+(?:[.,]\d+)?|(?:\d+\s+)?[¼½¾⅓⅔⅛⅜⅝⅞])\s*",
        "",
        value,
    ).strip()


def _page_url(title: str) -> str:
    return f"https://en.wikibooks.org/wiki/{title.replace(' ', '_')}"


def _title_key(title: str) -> str:
    return " ".join(title.replace("_", " ").casefold().split())


def _mapping(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError("expected an object in MediaWiki response")
    return cast(dict[str, object], value)


def _sequence(value: object) -> list[object]:
    if not isinstance(value, list):
        raise ValueError("expected a list in MediaWiki response")
    return cast(list[object], value)


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"missing {field} in MediaWiki response")
    return value


def _integer(value: object, field: str) -> int:
    if not isinstance(value, int):
        raise ValueError(f"missing {field} in MediaWiki response")
    return value


_NON_FOOD_LINKS = {
    _title_key(f"Cookbook:{title}")
    for title in (
        "Baking",
        "Beat",
        "Boiling",
        "Centimetre (cm)",
        "Chopping",
        "Creaming",
        "Cup",
        "Each",
        "Folding",
        "Gram",
        "Grating",
        "Inch",
        "Milliliter",
        "Mincing",
        "Ounce",
        "Oven",
        "Oven Temperatures",
        "Pinch",
        "Pound",
        "Slicing",
        "Tablespoon",
        "Teaspoon",
    )
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Import a bounded Wikibooks sample")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument(
        "--write",
        action="store_true",
        help="write eligible recipes to the local recipe inbox",
    )
    arguments = parser.parse_args()
    with Session(engine) as session:
        report = run_wikibooks_import(
            MediaWikiClient(),
            limit=arguments.limit,
            session=session,
            write=arguments.write,
        )
        if arguments.write:
            session.commit()
    print(json.dumps(asdict(report), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
