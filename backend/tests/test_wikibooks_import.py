from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from preppilot_api.catalog_data import load_catalog
from preppilot_api.catalog_seed import replace_catalog
from preppilot_api.models import Base, FoodSourceIdentifier, RecipeImport
from preppilot_api.wikibooks_import import (
    WikibooksPage,
    parse_recipe_page,
    run_wikibooks_import,
)


class FakeWikibooksSource:
    def fetch_recipe_pages(self, limit: int) -> tuple[WikibooksPage, ...]:
        return (_valid_page(), _invalid_page())[:limit]

    def resolve_page_ids(self, titles: set[str]) -> dict[str, int]:
        assert titles == {"Cookbook:Tomato"}
        return {"cookbook:tomato": 12345}


def test_dry_run_classifies_pages_without_writing() -> None:
    report = run_wikibooks_import(FakeWikibooksSource(), limit=2)

    assert report.discovered == 2
    assert report.eligible == 1
    assert report.rejected == 1
    assert report.imported == 0
    assert report.candidates[0].status == "eligible"
    assert report.candidates[1].reasons == ("missing_or_invalid_servings",)


def test_write_imports_eligible_recipe_idempotently_with_attribution() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    with Session(engine) as session, session.begin():
        replace_catalog(session, load_catalog())
        first = run_wikibooks_import(
            FakeWikibooksSource(), limit=2, session=session, write=True
        )
        second = run_wikibooks_import(
            FakeWikibooksSource(), limit=2, session=session, write=True
        )

        assert first.imported == 1
        assert second.duplicates == 1
        assert session.scalar(select(func.count()).select_from(RecipeImport)) == 1
        assert (
            session.scalar(select(func.count()).select_from(FoodSourceIdentifier))
            == 1
        )
        recipe_import = session.scalar(select(RecipeImport))
        assert recipe_import is not None
        source = recipe_import.raw_payload["source"]
        assert isinstance(source, dict)
        assert source["revision_id"] == 222
        assert source["license"] == "CC BY-SA 4.0"
        assert "wikitext" in recipe_import.raw_payload
        assert "ingredients" not in recipe_import.raw_payload


def test_parser_keeps_stable_ingredient_link_and_metric_amount() -> None:
    parsed, reasons = parse_recipe_page(_valid_page())

    assert reasons == ()
    assert parsed is not None
    assert parsed.servings == "2"
    assert parsed.instructions == "Mix tomatoes.\nServe."
    assert len(parsed.ingredients) == 1
    assert parsed.ingredients[0].amount == "200"
    assert parsed.ingredients[0].unit == "g"
    assert parsed.ingredients[0].source_title == "Cookbook:Tomato"


def test_parser_accepts_a_qualified_procedure_heading() -> None:
    page = _valid_page()
    qualified = WikibooksPage(
        page_id=page.page_id,
        title=page.title,
        revision_id=page.revision_id,
        revision_timestamp=page.revision_timestamp,
        url=page.url,
        wikitext=page.wikitext.replace("== Procedure ==", "== Procedure (brief) =="),
    )

    parsed, reasons = parse_recipe_page(qualified)

    assert reasons == ()
    assert parsed is not None


def _valid_page() -> WikibooksPage:
    return WikibooksPage(
        page_id=111,
        title="Cookbook:Test Tomatoes",
        revision_id=222,
        revision_timestamp="2026-09-02T10:00:00Z",
        url="https://en.wikibooks.org/wiki/Cookbook:Test_Tomatoes",
        wikitext="""{{Recipe summary|servings=2|time=5 minutes}}
== Ingredients ==
* 200 [[Cookbook:Gram|g]] [[Cookbook:Tomato|tomatoes]]
== Procedure ==
# Mix tomatoes.
# Serve.
[[Category:Recipes]]
""",
    )


def _invalid_page() -> WikibooksPage:
    return WikibooksPage(
        page_id=333,
        title="Cookbook:Missing Servings",
        revision_id=444,
        revision_timestamp="2026-09-02T10:00:00Z",
        url="https://en.wikibooks.org/wiki/Cookbook:Missing_Servings",
        wikitext="""{{Recipe summary|time=5 minutes}}
== Ingredients ==
* 200 [[Cookbook:Gram|g]] [[Cookbook:Tomato|tomatoes]]
== Procedure ==
# Mix tomatoes.
""",
    )
