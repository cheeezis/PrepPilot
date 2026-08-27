from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from preppilot_api.catalog_data import load_catalog
from preppilot_api.catalog_seed import replace_catalog
from preppilot_api.models import (
    Base,
    Food,
    Meal,
    MealIngredient,
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
