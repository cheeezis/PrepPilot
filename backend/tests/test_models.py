from preppilot_api.models import Base


def test_schema_contains_only_personal_recipes() -> None:
    assert set(Base.metadata.tables) == {"recipes"}


def test_recipe_source_is_optional() -> None:
    recipes = Base.metadata.tables["recipes"]
    assert recipes.columns["source_url"].nullable


def test_recipe_categories_are_stored_as_a_list() -> None:
    recipes = Base.metadata.tables["recipes"]
    assert "categories" in recipes.columns
    assert "category" not in recipes.columns


def test_recipe_keeps_personal_recipe_content_and_macros() -> None:
    columns = set(Base.metadata.tables["recipes"].columns.keys())
    assert {
        "calories_per_serving",
        "protein_per_serving",
        "carbs_per_serving",
        "fat_per_serving",
        "sugar_per_serving",
        "saturated_fat_per_serving",
        "fiber_per_serving",
        "salt_per_serving",
        "categories",
        "ingredients",
        "instructions",
        "source_url",
        "preparation_minutes",
        "cooking_minutes",
    } <= columns
    assert {
        "source_name",
        "external_id",
        "raw_payload",
        "content_hash",
        "imported_at",
        "license_name",
        "attribution_text",
    }.isdisjoint(columns)
