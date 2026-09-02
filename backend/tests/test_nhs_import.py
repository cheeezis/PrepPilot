from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

import preppilot_api.nhs_import as import_module
from preppilot_api.models import Base, Recipe
from preppilot_api.nhs_import import import_nhs_recipes, parse_recipe_page

PAGE = """
<html><head><script type="application/ld+json">
{"@type":"Recipe","name":"Test curry","recipeIngredient":["1 onion","2 tomatoes"],
"recipeInstructions":[{"text":"Chop vegetables.\\nCook everything."}]}
</script></head><body>
<p>Prep: 10 mins</p><p>Cook: 25 mins</p><p>Serves 4</p>
<ul><li>384kcal</li><li>22g protein</li><li>67g carbohydrate</li><li>3.5g fat</li></ul>
</body></html>
"""


def test_parses_complete_nhs_recipe_page() -> None:
    recipe = parse_recipe_page("https://example.test/recipe", PAGE)
    assert recipe.title == "Test curry"
    assert recipe.servings == 4
    assert recipe.ingredients == ["1 onion", "2 tomatoes"]
    assert recipe.instructions == ["Chop vegetables.", "Cook everything."]
    assert recipe.preparation_minutes == 10
    assert recipe.cooking_minutes == 25
    assert len(recipe.content_hash) == 64


def test_rejects_page_without_complete_macros() -> None:
    incomplete = PAGE.replace("22g protein", "protein unavailable")
    try:
        parse_recipe_page("https://example.test/recipe", incomplete)
    except ValueError as error:
        assert str(error) == "protein missing"
    else:
        raise AssertionError("incomplete recipe was accepted")


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
