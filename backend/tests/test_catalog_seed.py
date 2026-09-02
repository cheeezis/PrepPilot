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
    FoodSourceIdentifier,
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
            {food.concept_key for food in catalog.foods}
        )
        assert all(food.concept_id is not None for food in session.scalars(select(Food)))

        milk = session.scalar(
            select(FoodConcept)
            .join(Food, Food.concept_id == FoodConcept.id)
            .where(Food.catalog_key == "milk_1_5")
        )
        assert milk is not None
        assert (milk.key, milk.name) == ("milk", "Milk")


def test_seed_removes_only_unreferenced_concepts() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    with Session(engine) as session, session.begin():
        orphan = FoodConcept(key="old_profile_key", name="Old profile concept")
        referenced = FoodConcept(key="external_concept", name="External concept")
        session.add_all((orphan, referenced))
        session.flush()
        session.add(
            FoodSourceIdentifier(
                concept_id=referenced.id,
                source_name="test",
                external_id="ingredient-1",
                source_label="Test ingredient",
                source_url=None,
            )
        )

    with Session(engine) as session, session.begin():
        replace_catalog(session, load_catalog())

    with Session(engine) as session:
        concept_keys = set(session.scalars(select(FoodConcept.key)))

    assert "old_profile_key" not in concept_keys
    assert "external_concept" in concept_keys


def test_seed_moves_source_identity_from_legacy_profile_concept() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    with Session(engine) as session, session.begin():
        replace_catalog(session, load_catalog())
        milk = session.scalar(select(FoodConcept).where(FoodConcept.key == "milk"))
        assert milk is not None
        milk.key = "milk_1_5"
        milk.name = "Milk, 1.5% fat"
        generalized_milk = FoodConcept(key="milk", name="Milk")
        session.add(generalized_milk)
        session.flush()
        milk_profile = session.scalar(
            select(Food).where(Food.catalog_key == "milk_1_5")
        )
        assert milk_profile is not None
        milk_profile.concept_id = generalized_milk.id
        session.add(
            FoodSourceIdentifier(
                concept_id=milk.id,
                source_name="wikibooks",
                external_id="3612",
                source_label="Cookbook:Milk",
                source_url="https://en.wikibooks.org/wiki/Cookbook:Milk",
            )
        )

    with Session(engine) as session, session.begin():
        replace_catalog(session, load_catalog())

    with Session(engine) as session:
        identity = session.scalar(select(FoodSourceIdentifier))
        assert identity is not None
        concept = session.get(FoodConcept, identity.concept_id)
        concept_keys = set(session.scalars(select(FoodConcept.key)))

    assert concept is not None
    assert (concept.key, concept.name) == ("milk", "Milk")
    assert "milk_1_5" not in concept_keys


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
