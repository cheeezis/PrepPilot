from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from preppilot_api.models import Base, MealAssignment, Recipe, WeeklyPlan


def test_weekly_plan_persists_slots_and_batch_portions() -> None:
    engine = create_engine("sqlite+pysqlite://")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        recipe = Recipe(title="Meal Prep", servings=2, instructions=["Kochen."])
        plan = weekly_plan()
        plan.assignments = [
            MealAssignment(
                day_index=0,
                meal_role="lunch",
                slot_number=1,
                recipe=recipe,
                portion_number=1,
            ),
            MealAssignment(
                day_index=1,
                meal_role="dinner",
                slot_number=1,
                recipe=recipe,
                portion_number=2,
            ),
        ]
        session.add(plan)
        session.commit()

        stored = session.get(WeeklyPlan, plan.id)
        assert stored is not None
        assert stored.start_date == date(2026, 9, 7)
        assert stored.end_date == date(2026, 9, 13)
        assert [item.portion_number for item in stored.assignments] == [1, 2]

    engine.dispose()


@pytest.mark.parametrize(
    ("meal_role", "slot_number"),
    [("breakfast", 2), ("snack", 0), ("snack", 4)],
)
def test_weekly_plan_rejects_invalid_slots(
    meal_role: str, slot_number: int
) -> None:
    engine = create_engine("sqlite+pysqlite://")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        recipe = Recipe(title="Einzelgericht", servings=1, instructions=["Kochen."])
        plan = weekly_plan()
        plan.assignments = [
            MealAssignment(
                day_index=0,
                meal_role=meal_role,
                slot_number=slot_number,
                recipe=recipe,
                portion_number=None,
            )
        ]
        session.add(plan)
        with pytest.raises(IntegrityError):
            session.commit()

    engine.dispose()


def weekly_plan() -> WeeklyPlan:
    return WeeklyPlan(
        start_date=date(2026, 9, 7),
        end_date=date(2026, 9, 13),
        snacks_per_day=1,
        calories_maximum_kcal=Decimal("2500"),
        protein_minimum_g=Decimal("180"),
        carbohydrates_target_g=Decimal("250"),
        fat_maximum_g=Decimal("80"),
    )
