from preppilot_api.models import Base, MealRole, MeasurementUnit


def test_catalog_schema_contains_only_the_agreed_tables() -> None:
    assert set(Base.metadata.tables) == {
        "foods",
        "food_aliases",
        "food_portions",
        "meals",
        "meal_ingredients",
        "meal_roles",
    }


def test_link_tables_use_composite_primary_keys() -> None:
    food_aliases = Base.metadata.tables["food_aliases"]
    meal_ingredients = Base.metadata.tables["meal_ingredients"]
    meal_roles = Base.metadata.tables["meal_roles"]

    assert list(food_aliases.primary_key.columns.keys()) == [
        "source_name",
        "normalized_name",
    ]
    assert list(meal_ingredients.primary_key.columns.keys()) == ["meal_id", "food_id"]
    assert list(meal_roles.primary_key.columns.keys()) == ["meal_id", "role"]


def test_food_aliases_reference_internal_foods() -> None:
    food_aliases = Base.metadata.tables["food_aliases"]
    food_id = food_aliases.columns["food_id"]

    assert {foreign_key.target_fullname for foreign_key in food_id.foreign_keys} == {
        "foods.id"
    }


def test_food_portions_reference_internal_foods() -> None:
    food_portions = Base.metadata.tables["food_portions"]
    food_id = food_portions.columns["food_id"]

    assert {foreign_key.target_fullname for foreign_key in food_id.foreign_keys} == {
        "foods.id"
    }


def test_catalog_enums_match_the_planning_rules() -> None:
    assert [unit.value for unit in MeasurementUnit] == ["g", "ml"]
    assert [role.value for role in MealRole] == [
        "first_meal",
        "quick_lunch",
        "protein_snack",
        "main_meal",
        "late_snack",
    ]


def test_foods_and_meals_keep_source_metadata() -> None:
    source_columns = {
        "source_name",
        "source_reference",
        "source_retrieved_at",
    }

    assert source_columns <= set(Base.metadata.tables["foods"].columns.keys())
    assert source_columns <= set(Base.metadata.tables["meals"].columns.keys())


def test_imported_meals_keep_source_servings_and_measures() -> None:
    assert "source_servings" in Base.metadata.tables["meals"].columns
    assert "source_measure" in Base.metadata.tables["meal_ingredients"].columns
