from preppilot_api.models import Base


def test_schema_contains_only_the_recipe_catalog() -> None:
    assert set(Base.metadata.tables) == {"recipes"}


def test_recipe_source_identity_is_unique() -> None:
    recipes = Base.metadata.tables["recipes"]
    assert any(
        constraint.name == "uq_recipes_source_external"
        for constraint in recipes.constraints
    )


def test_recipe_keeps_source_macros_and_attribution() -> None:
    columns = set(Base.metadata.tables["recipes"].columns.keys())
    assert {
        "calories_per_serving",
        "protein_per_serving",
        "carbs_per_serving",
        "fat_per_serving",
        "ingredients",
        "instructions",
        "source_url",
        "license_name",
        "attribution_text",
    } <= columns
