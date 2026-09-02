from preppilot_api.models import Base, MealRole, MeasurementUnit


def test_schema_contains_catalog_and_import_inbox_tables() -> None:
    assert set(Base.metadata.tables) == {
        "foods",
        "meals",
        "meal_ingredients",
        "meal_portion_factors",
        "meal_roles",
        "recipe_imports",
        "recipe_import_ingredients",
        "food_aliases",
        "food_imports",
        "food_reference_items",
        "food_measure_defaults",
        "import_review_decisions",
    }


def test_link_tables_use_composite_primary_keys() -> None:
    meal_ingredients = Base.metadata.tables["meal_ingredients"]
    meal_portion_factors = Base.metadata.tables["meal_portion_factors"]
    meal_roles = Base.metadata.tables["meal_roles"]

    assert list(meal_ingredients.primary_key.columns.keys()) == ["meal_id", "food_id"]
    assert list(meal_portion_factors.primary_key.columns.keys()) == [
        "meal_id",
        "factor",
    ]
    assert list(meal_roles.primary_key.columns.keys()) == ["meal_id", "role"]


def test_catalog_entries_have_stable_unique_keys() -> None:
    foods = Base.metadata.tables["foods"]
    meals = Base.metadata.tables["meals"]

    assert foods.columns["catalog_key"].unique
    assert meals.columns["catalog_key"].unique


def test_imported_foods_keep_a_unique_food_import_source() -> None:
    foods = Base.metadata.tables["foods"]

    assert "origin" in foods.columns
    assert any(
        constraint.name == "uq_foods_source_food_import"
        for constraint in foods.constraints
    )


def test_imported_meals_keep_a_unique_recipe_source() -> None:
    meals = Base.metadata.tables["meals"]

    assert "origin" in meals.columns
    assert any(
        constraint.name == "uq_meals_source_recipe_import"
        for constraint in meals.constraints
    )


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
