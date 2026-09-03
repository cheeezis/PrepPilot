from dataclasses import dataclass
from decimal import Decimal
from itertools import combinations
from typing import Literal

from preppilot_api.nutrition import Nutrients
from preppilot_api.recipe_repository import RecipeDefinition

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
class PlannedRecipe:
    recipe: RecipeDefinition
    portions: int
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
    recipes: tuple[PlannedRecipe, ...]


def generate_day_plans(
    targets: PlanTargets,
    recipes: tuple[RecipeDefinition, ...],
    limit: int = 3,
) -> tuple[DayPlan, ...]:
    if targets.meal_count < 1:
        raise ValueError("meal_count must be positive")
    if limit < 1:
        raise ValueError("limit must be positive")

    candidates: list[DayPlan] = []
    for selected in combinations(recipes, targets.meal_count):
        minimum = sum((recipe.nutrients for recipe in selected), start=Nutrients())
        if not _nutrient_range_can_reach_outer_limits(
            minimum, minimum.scaled(2), targets
        ):
            continue

        additional_nutrients: tuple[Nutrients, ...] = (Nutrients(),)
        for recipe in selected:
            additional_nutrients += tuple(
                nutrients + recipe.nutrients for nutrients in additional_nutrients
            )

        for portion_mask, additional in enumerate(additional_nutrients):
            nutrients = minimum + additional
            if not _is_within_outer_limits(nutrients, targets):
                continue
            portions = tuple(
                2 if portion_mask & (1 << index) else 1
                for index in range(targets.meal_count)
            )
            planned = tuple(
                PlannedRecipe(
                    recipe=recipe,
                    portions=portion_count,
                    nutrients=recipe.nutrients.scaled(portion_count),
                )
                for recipe, portion_count in zip(selected, portions, strict=True)
            )
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
                f"{item.recipe.id}:{item.portions}" for item in planned
            )
            candidates.append(
                DayPlan(
                    status=status,
                    score=_calculate_score(nutrients, targets),
                    stable_key=stable_key,
                    nutrients=nutrients,
                    evaluations=evaluations,
                    recipes=planned,
                )
            )
            candidates.sort(key=_plan_sort_key)
            del candidates[limit:]

    return tuple(candidates)


def _combination_can_reach_outer_limits(
    recipes: tuple[RecipeDefinition, ...], targets: PlanTargets
) -> bool:
    minimum = sum((recipe.nutrients for recipe in recipes), start=Nutrients())
    return _nutrient_range_can_reach_outer_limits(
        minimum, minimum.scaled(2), targets
    )


def _nutrient_range_can_reach_outer_limits(
    minimum: Nutrients, maximum: Nutrients, targets: PlanTargets
) -> bool:
    return (
        maximum.calories >= targets.calories * Decimal("0.9")
        and minimum.calories <= targets.calories * Decimal("1.1")
        and maximum.protein >= targets.protein_minimum * Decimal("0.9")
        and maximum.fat >= targets.fat_maximum * Decimal("0.7")
        and minimum.fat <= targets.fat_maximum * Decimal("1.1")
        and maximum.carbs >= targets.carbs * Decimal("0.5")
        and minimum.carbs <= targets.carbs * Decimal("1.5")
    )


def _plan_sort_key(candidate: DayPlan) -> tuple[int, Decimal, str]:
    return (
        0 if candidate.status == "valid" else 1,
        candidate.score,
        candidate.stable_key,
    )


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
            "calories",
            "hard",
            nutrients.calories,
            targets.calories,
            calorie_minimum,
            calorie_maximum,
            calorie_minimum <= nutrients.calories <= calorie_maximum,
        ),
        RuleEvaluation(
            "protein",
            "hard",
            nutrients.protein,
            None,
            targets.protein_minimum,
            None,
            nutrients.protein >= targets.protein_minimum,
        ),
        RuleEvaluation(
            "fat",
            "hard",
            nutrients.fat,
            None,
            fat_minimum,
            targets.fat_maximum,
            fat_minimum <= nutrients.fat <= targets.fat_maximum,
        ),
        RuleEvaluation(
            "carbs",
            "soft",
            nutrients.carbs,
            targets.carbs,
            carb_minimum,
            carb_maximum,
            carb_minimum <= nutrients.carbs <= carb_maximum,
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
        abs(nutrients.calories - targets.calories) / (targets.calories * Decimal("0.1"))
    )
    fat_minimum = targets.fat_maximum * Decimal("0.8")
    fat_distance = (
        fat_minimum - nutrients.fat
        if nutrients.fat < fat_minimum
        else nutrients.fat - targets.fat_maximum
        if nutrients.fat > targets.fat_maximum
        else Decimal(0)
    )
    fat_deviation = _cap_at_one(fat_distance / (targets.fat_maximum * Decimal("0.1")))
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
