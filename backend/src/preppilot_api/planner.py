from dataclasses import dataclass
from decimal import Decimal
from itertools import product
from typing import Literal

from preppilot_api.catalog_data import Catalog, MealDefinition
from preppilot_api.models import MealRole
from preppilot_api.nutrition import Nutrients, calculate_meal_nutrients

PlanStatus = Literal["valid", "approximation"]
RuleKind = Literal["hard", "soft"]
Metric = Literal["calories", "protein", "fat", "carbs"]


@dataclass(frozen=True)
class PlanTargets:
    calories: Decimal
    protein_minimum: Decimal
    fat_maximum: Decimal
    carbs: Decimal
    meal_count: int


@dataclass(frozen=True)
class PlannedMeal:
    meal: MealDefinition
    role: MealRole
    portion_factor: Decimal
    nutrients: Nutrients


@dataclass(frozen=True)
class RuleEvaluation:
    metric: Metric
    kind: RuleKind
    actual: Decimal
    target: Decimal | None
    minimum: Decimal | None
    maximum: Decimal | None
    satisfied: bool


@dataclass(frozen=True)
class DayPlan:
    status: PlanStatus
    score: Decimal
    stable_key: str
    nutrients: Nutrients
    evaluations: tuple[RuleEvaluation, ...]
    meals: tuple[PlannedMeal, ...]


ROLE_STRUCTURES: dict[int, tuple[MealRole, ...]] = {
    3: (
        MealRole.FIRST_MEAL,
        MealRole.QUICK_LUNCH,
        MealRole.MAIN_MEAL,
    ),
    4: (
        MealRole.FIRST_MEAL,
        MealRole.QUICK_LUNCH,
        MealRole.PROTEIN_SNACK,
        MealRole.MAIN_MEAL,
    ),
    5: (
        MealRole.FIRST_MEAL,
        MealRole.QUICK_LUNCH,
        MealRole.PROTEIN_SNACK,
        MealRole.PROTEIN_SNACK,
        MealRole.MAIN_MEAL,
    ),
    6: (
        MealRole.FIRST_MEAL,
        MealRole.QUICK_LUNCH,
        MealRole.PROTEIN_SNACK,
        MealRole.PROTEIN_SNACK,
        MealRole.MAIN_MEAL,
        MealRole.LATE_SNACK,
    ),
}


def generate_day_plans(
    targets: PlanTargets, catalog: Catalog, limit: int = 3
) -> tuple[DayPlan, ...]:
    if targets.meal_count not in ROLE_STRUCTURES:
        raise ValueError("meal_count must be between 3 and 6")
    if limit < 1:
        raise ValueError("limit must be positive")

    foods = {food.key: food for food in catalog.foods}
    structures = ROLE_STRUCTURES[targets.meal_count]
    options_by_role = {
        role: tuple(
            PlannedMeal(
                meal=meal,
                role=role,
                portion_factor=factor,
                nutrients=calculate_meal_nutrients(meal, foods).scaled(factor),
            )
            for meal in catalog.meals
            if role in meal.roles
            for factor in meal.portion_factors
        )
        for role in set(structures)
    }

    candidates: list[DayPlan] = []
    seen_signatures: set[tuple[tuple[str, str, Decimal], ...]] = set()
    for meals in product(*(options_by_role[role] for role in structures)):
        meal_keys = [planned_meal.meal.key for planned_meal in meals]
        if len(meal_keys) != len(set(meal_keys)):
            continue

        signature = tuple(
            sorted(
                (
                    planned_meal.role.value,
                    planned_meal.meal.key,
                    planned_meal.portion_factor,
                )
                for planned_meal in meals
            )
        )
        if signature in seen_signatures:
            continue
        seen_signatures.add(signature)

        nutrients = sum(
            (planned_meal.nutrients for planned_meal in meals), start=Nutrients()
        )
        if not _is_within_outer_limits(nutrients, targets):
            continue

        evaluations = _evaluate_rules(nutrients, targets)
        status: PlanStatus = (
            "valid"
            if all(
                evaluation.satisfied
                for evaluation in evaluations
                if evaluation.kind == "hard"
            )
            else "approximation"
        )
        stable_key = "|".join(
            f"{role}:{meal_key}:{factor}" for role, meal_key, factor in signature
        )
        candidates.append(
            DayPlan(
                status=status,
                score=_calculate_score(nutrients, targets),
                stable_key=stable_key,
                nutrients=nutrients,
                evaluations=evaluations,
                meals=meals,
            )
        )

    candidates.sort(
        key=lambda candidate: (
            0 if candidate.status == "valid" else 1,
            candidate.score,
            candidate.stable_key,
        )
    )
    return tuple(candidates[:limit])


def _evaluate_rules(
    nutrients: Nutrients, targets: PlanTargets
) -> tuple[RuleEvaluation, ...]:
    calorie_minimum = targets.calories * Decimal("0.95")
    calorie_maximum = targets.calories * Decimal("1.05")
    fat_minimum = targets.fat_maximum * Decimal("0.8")
    carb_minimum = targets.carbs * Decimal("0.8")
    carb_maximum = targets.carbs * Decimal("1.2")
    return (
        RuleEvaluation(
            metric="calories",
            kind="hard",
            actual=nutrients.calories,
            target=targets.calories,
            minimum=calorie_minimum,
            maximum=calorie_maximum,
            satisfied=calorie_minimum
            <= nutrients.calories
            <= calorie_maximum,
        ),
        RuleEvaluation(
            metric="protein",
            kind="hard",
            actual=nutrients.protein,
            target=None,
            minimum=targets.protein_minimum,
            maximum=None,
            satisfied=nutrients.protein >= targets.protein_minimum,
        ),
        RuleEvaluation(
            metric="fat",
            kind="hard",
            actual=nutrients.fat,
            target=None,
            minimum=fat_minimum,
            maximum=targets.fat_maximum,
            satisfied=fat_minimum <= nutrients.fat <= targets.fat_maximum,
        ),
        RuleEvaluation(
            metric="carbs",
            kind="soft",
            actual=nutrients.carbs,
            target=targets.carbs,
            minimum=carb_minimum,
            maximum=carb_maximum,
            satisfied=carb_minimum <= nutrients.carbs <= carb_maximum,
        ),
    )


def _is_within_outer_limits(nutrients: Nutrients, targets: PlanTargets) -> bool:
    return (
        targets.calories * Decimal("0.9")
        <= nutrients.calories
        <= targets.calories * Decimal("1.1")
        and nutrients.protein >= targets.protein_minimum * Decimal("0.9")
        and targets.fat_maximum * Decimal("0.7")
        <= nutrients.fat
        <= targets.fat_maximum * Decimal("1.1")
        and targets.carbs * Decimal("0.5")
        <= nutrients.carbs
        <= targets.carbs * Decimal("1.5")
    )


def _calculate_score(nutrients: Nutrients, targets: PlanTargets) -> Decimal:
    protein_deviation = _cap_at_one(
        max(Decimal(0), targets.protein_minimum - nutrients.protein)
        / (targets.protein_minimum * Decimal("0.1"))
    )
    calorie_deviation = _cap_at_one(
        abs(nutrients.calories - targets.calories)
        / (targets.calories * Decimal("0.1"))
    )

    fat_minimum = targets.fat_maximum * Decimal("0.8")
    if nutrients.fat < fat_minimum:
        fat_distance = fat_minimum - nutrients.fat
    elif nutrients.fat > targets.fat_maximum:
        fat_distance = nutrients.fat - targets.fat_maximum
    else:
        fat_distance = Decimal(0)
    fat_deviation = _cap_at_one(
        fat_distance / (targets.fat_maximum * Decimal("0.1"))
    )

    carb_deviation = _cap_at_one(
        abs(nutrients.carbs - targets.carbs) / (targets.carbs * Decimal("0.5"))
    )
    return (
        protein_deviation * Decimal("0.4")
        + calorie_deviation * Decimal("0.3")
        + fat_deviation * Decimal("0.2")
        + carb_deviation * Decimal("0.1")
    )


def _cap_at_one(value: Decimal) -> Decimal:
    return min(value, Decimal(1))
