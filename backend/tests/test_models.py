from preppilot_api.models import Base, MealRole, MeasurementUnit


def test_catalog_schema_contains_only_the_mvp_tables() -> None:
    assert set(Base.metadata.tables) == {
        "foods",
        "meals",
        "meal_ingredients",
        "meal_roles",
    }


def test_link_tables_use_composite_primary_keys() -> None:
    meal_ingredients = Base.metadata.tables["meal_ingredients"]
    meal_roles = Base.metadata.tables["meal_roles"]

    assert list(meal_ingredients.primary_key.columns.keys()) == ["meal_id", "food_id"]
    assert list(meal_roles.primary_key.columns.keys()) == ["meal_id", "role"]


def test_catalog_entries_have_stable_unique_keys() -> None:
    foods = Base.metadata.tables["foods"]
    meals = Base.metadata.tables["meals"]

    assert foods.columns["catalog_key"].unique
    assert meals.columns["catalog_key"].unique


def test_catalog_enums_match_the_planning_rules() -> None:
    assert [unit.value for unit in MeasurementUnit] == ["g", "ml"]
    assert [role.value for role in MealRole] == [
        "first_meal",
        "quick_lunch",
        "protein_snack",
        "main_meal",
        "late_snack",
    ]


def test_only_foods_keep_source_metadata() -> None:
    foods = Base.metadata.tables["foods"]
    meals = Base.metadata.tables["meals"]

    assert {"source_name", "source_reference"} <= set(foods.columns.keys())
    assert "source_name" not in meals.columns
    assert "source_reference" not in meals.columns
