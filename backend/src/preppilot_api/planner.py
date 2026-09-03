from dataclasses import dataclass
from decimal import Decimal
from itertools import product
from typing import Literal

from preppilot_api.nutrition import Nutrients
from preppilot_api.recipe_repository import RecipeCategory, RecipeDefinition

PlanStatus = Literal["valid", "approximation"]
RuleKind = Literal["hard", "soft"]
Metric = Literal["calories", "protein", "fat", "carbs"]
DEFAULT_MEAL_CATEGORIES: tuple[RecipeCategory, ...] = (
    "breakfast",
    "lunch",
    "dinner",
)
FLEXIBLE_CHOICE_LIMIT = 24


@dataclass(frozen=True)
class PlanTargets:
    calories: Decimal
    protein_minimum: Decimal
    fat_maximum: Decimal
    carbs: Decimal


@dataclass(frozen=True)
class PlannedRecipe:
    recipe: RecipeDefinition
    category: RecipeCategory
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


@dataclass(frozen=True)
class WeekPlan:
    days: tuple[DayPlan, ...]


@dataclass(frozen=True)
class _MealChoice:
    position: int
    category: RecipeCategory
    recipe: RecipeDefinition
    portions: int
    nutrients: Nutrients


def generate_day_plans(
    targets: PlanTargets,
    recipes: tuple[RecipeDefinition, ...],
    meal_categories: tuple[RecipeCategory, ...] = DEFAULT_MEAL_CATEGORIES,
    limit: int = 3,
) -> tuple[DayPlan, ...]:
    if limit < 1:
        raise ValueError("limit must be positive")
    if not meal_categories:
        raise ValueError("at least one meal category is required")
    if len(set(meal_categories)) != len(meal_categories):
        raise ValueError("meal categories must be unique")

    if len(meal_categories) <= 3:
        return _generate_exact_day_plans(
            targets, recipes, meal_categories, limit
        )

    candidates: list[DayPlan] = []
    choice_groups = [
        tuple(
            _MealChoice(
                position=position,
                category=category,
                recipe=recipe,
                portions=portions,
                nutrients=recipe.nutrients.scaled(portions),
            )
            for recipe in recipes
            if category in recipe.categories
            for portions in (1, 2)
        )
        for position, category in enumerate(meal_categories)
    ]
    if any(not group for group in choice_groups):
        return ()

    choice_groups = [
        _shortlist_choices(group, targets, len(meal_categories))
        for group in choice_groups
    ]

    choice_groups.sort(key=len)
    suffix_minimum = [Nutrients() for _ in range(len(choice_groups) + 1)]
    suffix_maximum = [Nutrients() for _ in range(len(choice_groups) + 1)]
    for index in range(len(choice_groups) - 1, -1, -1):
        group_minimum, group_maximum = _choice_group_bounds(choice_groups[index])
        suffix_minimum[index] = group_minimum + suffix_minimum[index + 1]
        suffix_maximum[index] = group_maximum + suffix_maximum[index + 1]

    def search(
        group_index: int,
        selected: tuple[_MealChoice, ...],
        selected_ids: frozenset[int],
        nutrients: Nutrients,
    ) -> None:
        if not _nutrient_range_can_reach_outer_limits(
            nutrients + suffix_minimum[group_index],
            nutrients + suffix_maximum[group_index],
            targets,
        ):
            return
        if group_index == len(choice_groups):
            _keep_plan_candidate(candidates, selected, nutrients, targets, limit)
            return

        for choice in choice_groups[group_index]:
            if choice.recipe.id in selected_ids:
                continue
            search(
                group_index + 1,
                selected + (choice,),
                selected_ids | {choice.recipe.id},
                nutrients + choice.nutrients,
            )

    search(0, (), frozenset(), Nutrients())
    return tuple(candidates)


def generate_week_plan(
    targets: PlanTargets,
    recipes: tuple[RecipeDefinition, ...],
    day_count: int,
    meal_categories: tuple[RecipeCategory, ...] = DEFAULT_MEAL_CATEGORIES,
) -> WeekPlan | None:
    if not 3 <= day_count <= 7:
        raise ValueError("day count must be between 3 and 7")

    planned_days: list[DayPlan] = []
    used_recipe_ids: set[int] = set()
    while len(planned_days) < day_count:
        available_recipes = tuple(
            recipe for recipe in recipes if recipe.id not in used_recipe_ids
        )
        plans = generate_day_plans(
            targets,
            available_recipes,
            meal_categories,
            limit=1,
        )
        if not plans:
            return None

        plan = plans[0]
        block_size = min(2, day_count - len(planned_days))
        planned_days.extend(plan for _ in range(block_size))
        used_recipe_ids.update(item.recipe.id for item in plan.recipes)

    return WeekPlan(days=tuple(planned_days))


def _generate_exact_day_plans(
    targets: PlanTargets,
    recipes: tuple[RecipeDefinition, ...],
    meal_categories: tuple[RecipeCategory, ...],
    limit: int,
) -> tuple[DayPlan, ...]:
    candidates: list[DayPlan] = []
    recipes_by_category = tuple(
        tuple(recipe for recipe in recipes if category in recipe.categories)
        for category in meal_categories
    )
    for selected in product(*recipes_by_category):
        if len({recipe.id for recipe in selected}) != len(selected):
            continue
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
            choices = tuple(
                _MealChoice(
                    position=index,
                    category=meal_categories[index],
                    recipe=recipe,
                    portions=(2 if portion_mask & (1 << index) else 1),
                    nutrients=recipe.nutrients.scaled(
                        2 if portion_mask & (1 << index) else 1
                    ),
                )
                for index, recipe in enumerate(selected)
            )
            _keep_plan_candidate(candidates, choices, nutrients, targets, limit)
    return tuple(candidates)


def _shortlist_choices(
    choices: tuple[_MealChoice, ...],
    targets: PlanTargets,
    meal_count: int,
) -> tuple[_MealChoice, ...]:
    snack_selected = any(choice.category == "snack" for choice in choices)
    if snack_selected and meal_count > 1:
        share = (
            Decimal("0.15")
            if choices[0].category == "snack"
            else Decimal("0.85") / Decimal(meal_count - 1)
        )
    else:
        share = Decimal(1) / Decimal(meal_count)

    def suitability(choice: _MealChoice) -> tuple[Decimal, int, int]:
        nutrients = choice.nutrients
        score = (
            abs(nutrients.calories - targets.calories * share) / targets.calories
            + abs(nutrients.protein - targets.protein_minimum * share)
            / targets.protein_minimum
            + abs(nutrients.fat - targets.fat_maximum * share) / targets.fat_maximum
            + abs(nutrients.carbs - targets.carbs * share) / targets.carbs
        )
        return score, choice.recipe.id, choice.portions

    return tuple(sorted(choices, key=suitability)[:FLEXIBLE_CHOICE_LIMIT])


def _choice_group_bounds(
    choices: tuple[_MealChoice, ...],
) -> tuple[Nutrients, Nutrients]:
    return (
        Nutrients(
            calories=min(choice.nutrients.calories for choice in choices),
            protein=min(choice.nutrients.protein for choice in choices),
            carbs=min(choice.nutrients.carbs for choice in choices),
            fat=min(choice.nutrients.fat for choice in choices),
        ),
        Nutrients(
            calories=max(choice.nutrients.calories for choice in choices),
            protein=max(choice.nutrients.protein for choice in choices),
            carbs=max(choice.nutrients.carbs for choice in choices),
            fat=max(choice.nutrients.fat for choice in choices),
        ),
    )


def _keep_plan_candidate(
    candidates: list[DayPlan],
    selected: tuple[_MealChoice, ...],
    nutrients: Nutrients,
    targets: PlanTargets,
    limit: int,
) -> None:
    if not _is_within_outer_limits(nutrients, targets):
        return
    planned = tuple(
        PlannedRecipe(
            recipe=choice.recipe,
            category=choice.category,
            portions=choice.portions,
            nutrients=choice.nutrients,
        )
        for choice in sorted(selected, key=lambda item: item.position)
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
        f"{item.category}:{item.recipe.id}:{item.portions}" for item in planned
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
