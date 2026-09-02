import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from preppilot_api.catalog_data import load_catalog
from preppilot_api.catalog_repository import (
    CatalogUnavailableError,
    load_catalog_from_database,
)
from preppilot_api.catalog_seed import replace_catalog
from preppilot_api.models import (
    Base,
    Food,
    FoodAlias,
    FoodConcept,
    FoodMeasureDefault,
    Meal,
    MealIngredient,
    MealPortionFactor,
    MealRoleAssignment,
)


def test_replaces_database_catalog_reproducibly() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    catalog = load_catalog()

    with Session(engine) as session, session.begin():
        replace_catalog(session, catalog)
    with Session(engine) as session, session.begin():
        replace_catalog(session, catalog)

    with Session(engine) as session:
        assert session.scalar(select(func.count()).select_from(Food)) == len(
            catalog.foods
        )
        assert session.scalar(select(func.count()).select_from(Meal)) == len(
            catalog.meals
        )
        assert session.scalar(select(func.count()).select_from(MealIngredient)) == sum(
            len(meal.ingredients) for meal in catalog.meals
        )
        assert session.scalar(
            select(func.count()).select_from(MealRoleAssignment)
        ) == sum(len(meal.roles) for meal in catalog.meals)
        assert session.scalar(
            select(func.count()).select_from(MealPortionFactor)
        ) == sum(len(meal.portion_factors) for meal in catalog.meals)
        assert session.scalar(select(func.count()).select_from(FoodAlias)) == sum(
            len(food.aliases) for food in catalog.foods
        )
        assert session.scalar(
            select(func.count()).select_from(FoodMeasureDefault)
        ) == sum(len(food.measure_defaults) for food in catalog.foods)
        assert session.scalar(select(func.count()).select_from(FoodConcept)) == len(
            catalog.foods
        )
        assert all(food.concept_id is not None for food in session.scalars(select(Food)))


def test_seed_keeps_normalized_ingredient_amounts() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    with Session(engine) as session, session.begin():
        replace_catalog(session, load_catalog())

    with Session(engine) as session:
        amount = session.scalar(
            select(MealIngredient.amount)
            .join(Meal, Meal.id == MealIngredient.meal_id)
            .join(Food, Food.id == MealIngredient.food_id)
            .where(
                Meal.catalog_key == "whey_shake",
                Food.catalog_key == "milk_1_5",
            )
        )

    assert amount == 300


def test_loads_seeded_catalog_from_database() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    source_catalog = load_catalog()

    with Session(engine) as session, session.begin():
        replace_catalog(session, source_catalog)
    with Session(engine) as session:
        database_catalog = load_catalog_from_database(session)

    assert {food.key for food in database_catalog.foods} == {
        food.key for food in source_catalog.foods
    }
    assert {meal.key for meal in database_catalog.meals} == {
        meal.key for meal in source_catalog.meals
    }
    assert sum(len(meal.ingredients) for meal in database_catalog.meals) == sum(
        len(meal.ingredients) for meal in source_catalog.meals
    )


def test_rejects_empty_database_catalog() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    with Session(engine) as session, pytest.raises(CatalogUnavailableError):
        load_catalog_from_database(session)
