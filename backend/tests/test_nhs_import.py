from decimal import Decimal

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

import preppilot_api.nhs_import as import_module
from preppilot_api.models import Base, Recipe
from preppilot_api.nhs_import import (
    _instructions,
    import_nhs_recipes,
    parse_recipe_page,
)

PAGE = """
<html><head><script type="application/ld+json">
{"@type":"Recipe","name":"Test curry","recipeIngredient":["1 onion","2 tomatoes"],
"recipeInstructions":[{"text":"Chop vegetables.\\nCook everything."}]}
</script></head><body>
<p>Prep: 10 mins</p><p>Cook: 25 mins</p><p>Serves 4</p>
<ul><li>384kcal</li><li>22g protein</li>
<li>67g carbohydrate, of which 8g sugars</li>
<li>3.5g fat, of which 1g saturates</li><li>6.2g fibre</li><li>0.7g salt</li></ul>
</body></html>
"""


def test_parses_complete_nhs_recipe_page() -> None:
    recipe = parse_recipe_page("https://example.test/recipe", PAGE)
    assert recipe.title == "Test curry"
    assert recipe.category == "dinner"
    assert recipe.servings == 4
    assert recipe.ingredients == ["1 onion", "2 tomatoes"]
    assert recipe.instructions == ["Chop vegetables.", "Cook everything."]
    assert recipe.preparation_minutes == 10
    assert recipe.cooking_minutes == 25
    assert recipe.sugar == 8
    assert recipe.saturated_fat == 1
    assert recipe.fiber == Decimal("6.2")
    assert recipe.salt == Decimal("0.7")
    assert len(recipe.content_hash) == 64


def test_assigns_category_from_the_approved_nhs_collection() -> None:
    recipe = parse_recipe_page(
        "https://www.nhs.uk/healthier-families/recipes/super-scrambled-eggs/",
        PAGE,
    )

    assert recipe.category == "breakfast"


def test_rejects_page_without_complete_macros() -> None:
    incomplete = PAGE.replace("22g protein", "protein unavailable")
    try:
        parse_recipe_page("https://example.test/recipe", incomplete)
    except ValueError as error:
        assert str(error) == "protein missing"
    else:
        raise AssertionError("incomplete recipe was accepted")


def test_rejects_energetically_impossible_macros() -> None:
    inconsistent = PAGE.replace("3.5g fat", "79g fat")

    try:
        parse_recipe_page("https://example.test/recipe", inconsistent)
    except ValueError as error:
        assert str(error) == "nutrient energy inconsistent"
    else:
        raise AssertionError("inconsistent nutrient values were accepted")


def test_keeps_structured_how_to_steps_separate() -> None:
    instructions = [
        {"@type": "HowToStep", "text": "Chop the vegetables."},
        {"@type": "HowToStep", "text": "Cook everything."},
    ]

    assert _instructions(instructions) == [
        "Chop the vegetables.",
        "Cook everything.",
    ]


def test_prefers_visible_nhs_method_list_over_joined_json_ld_text() -> None:
    page = PAGE.replace(
        "</body>",
        """
        <div class="bh-recipe-instructions__method">
          <h2>Method</h2>
          <ol>
            <li><p>Prepare the pan.</p></li>
            <li>
              <p>Add the ingredients.</p>
              <div class="nhsuk-inset-text">
                <span class="nhsuk-u-visually-hidden">Information:</span>
                <p>A useful optional tip.</p>
              </div>
            </li>
          </ol>
        </div>
        </body>
        """,
    )

    recipe = parse_recipe_page("https://example.test/recipe", page)

    assert recipe.instructions == [
        "Prepare the pan.",
        "Add the ingredients. Information: A useful optional tip.",
    ]


def test_reads_steps_from_nested_how_to_section() -> None:
    instructions = [
        {
            "@type": "HowToSection",
            "name": "Method",
            "itemListElement": [
                {"@type": "HowToStep", "text": "Prepare the pan."},
                {"@type": "HowToStep", "text": "Add the ingredients."},
            ],
        }
    ]

    assert _instructions(instructions) == [
        "Prepare the pan.",
        "Add the ingredients.",
    ]


def test_splits_only_clear_numbered_step_markers() -> None:
    assert _instructions(
        "Step 1. Prepare the pan. Step 2. Add the ingredients. 3. Serve."
    ) == ["Prepare the pan.", "Add the ingredients.", "Serve."]


def test_keeps_unstructured_prose_as_one_step() -> None:
    assert _instructions(
        "Prepare the pan. Add the ingredients and cook until tender."
    ) == ["Prepare the pan. Add the ingredients and cook until tender."]


def test_rejects_missing_instructions() -> None:
    try:
        _instructions([])
    except ValueError as error:
        assert str(error) == "instructions missing"
    else:
        raise AssertionError("missing instructions were accepted")


def test_identical_second_import_is_idempotent(monkeypatch) -> None:
    monkeypatch.setattr(
        import_module, "NHS_RECIPE_URLS", ("https://example.test/recipe",)
    )
    monkeypatch.setattr(import_module, "fetch_recipe_page", lambda url: PAGE)
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        assert import_nhs_recipes(session)[0].status == "created"
        assert import_nhs_recipes(session)[0].status == "unchanged"
        assert session.scalar(select(func.count()).select_from(Recipe)) == 1


def test_import_keeps_rejections_out_of_the_recipe_inventory(monkeypatch) -> None:
    urls = ("https://example.test/complete", "https://example.test/incomplete")
    monkeypatch.setattr(import_module, "NHS_RECIPE_URLS", urls)
    monkeypatch.setattr(
        import_module,
        "fetch_recipe_page",
        lambda url: PAGE if url == urls[0] else PAGE.replace("22g protein", ""),
    )
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        items = import_nhs_recipes(session)

        assert [item.status for item in items] == ["created", "rejected"]
        assert items[1].reason == "protein missing"
        assert session.scalar(select(func.count()).select_from(Recipe)) == 1
