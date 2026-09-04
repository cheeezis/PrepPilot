from dataclasses import dataclass
from decimal import Decimal
from itertools import product

from preppilot_api.models import MealAssignment, Recipe
from preppilot_api.nutrition import Nutrients, calculate_recipe_nutrition

MEAL_ROLES = ("breakfast", "lunch", "dinner")
MAX_BATCH_SCHEDULES = 10_000


class PlanGenerationError(Exception):
    pass


@dataclass(frozen=True)
class MealSlot:
    day_index: int
    meal_role: str
    slot_number: int


@dataclass(frozen=True)
class NutritionTargets:
    calories_maximum_kcal: Decimal
    protein_minimum_g: Decimal
    carbohydrates_target_g: Decimal
    fat_maximum_g: Decimal


Score = tuple[Decimal, Decimal, Decimal, Decimal, int, tuple[int, ...]]


def generate_assignments(
    recipes: list[Recipe], snacks_per_day: int, targets: NutritionTargets
) -> list[MealAssignment]:
    slots = _meal_slots(snacks_per_day)
    batches = sorted(
        (recipe for recipe in recipes if recipe.servings > 1),
        key=lambda recipe: recipe.id,
    )
    singles = sorted(
        (recipe for recipe in recipes if recipe.servings == 1),
        key=lambda recipe: recipe.id,
    )
    nutrition = {
        recipe.id: calculate_recipe_nutrition(recipe).per_serving
        for recipe in recipes
    }

    best: tuple[Score, dict[MealSlot, MealAssignment]] | None = None
    first_error: PlanGenerationError | None = None
    for batch_assignments in _batch_schedules(batches, slots):
        try:
            assignments = _fill_single_slots(
                slots, batch_assignments, singles, nutrition, targets
            )
        except PlanGenerationError as error:
            if first_error is None:
                first_error = error
            continue
        score = _plan_score(assignments, nutrition, targets)
        if best is None or score < best[0]:
            best = (score, assignments)

    if best is None:
        raise first_error or PlanGenerationError(
            "Kein vollständiger Wochenplan mit den vorhandenen Rezepten möglich"
        )
    return [best[1][slot] for slot in slots]


def _batch_schedules(
    recipes: list[Recipe], slots: list[MealSlot]
) -> list[dict[MealSlot, MealAssignment]]:
    schedules: list[dict[MealSlot, MealAssignment]] = []

    def visit(
        assignments: dict[MealSlot, MealAssignment], remaining: tuple[Recipe, ...]
    ) -> None:
        if len(schedules) >= MAX_BATCH_SCHEDULES:
            return
        schedules.append(assignments)
        for index, recipe in enumerate(remaining):
            compatible = _compatible_slots(recipe, slots, assignments)
            if len(compatible) < recipe.servings:
                continue
            extended = dict(assignments)
            for portion_number, slot in enumerate(
                compatible[: recipe.servings], start=1
            ):
                extended[slot] = _assignment(slot, recipe, portion_number)
            visit(extended, remaining[:index] + remaining[index + 1 :])

    visit({}, tuple(recipes))
    return schedules


def _compatible_slots(
    recipe: Recipe,
    slots: list[MealSlot],
    assignments: dict[MealSlot, MealAssignment],
) -> list[MealSlot]:
    roles = {item.meal_role for item in recipe.meal_roles}
    return [
        slot
        for slot in slots
        if slot not in assignments and slot.meal_role in roles
    ]


def _fill_single_slots(
    slots: list[MealSlot],
    batch_assignments: dict[MealSlot, MealAssignment],
    recipes: list[Recipe],
    nutrition: dict[int, Nutrients],
    targets: NutritionTargets,
) -> dict[MealSlot, MealAssignment]:
    assignments = dict(batch_assignments)
    for day_index in range(7):
        empty_slots = [
            slot
            for slot in slots
            if slot.day_index == day_index and slot not in assignments
        ]
        choices: list[list[Recipe]] = []
        for slot in empty_slots:
            compatible = [
                recipe
                for recipe in recipes
                if slot.meal_role in {role.meal_role for role in recipe.meal_roles}
            ]
            if not compatible:
                raise PlanGenerationError(
                    f"Kein Einzelrezept für {slot_label(slot)} verfügbar"
                )
            choices.append(compatible)

        fixed = [
            item
            for slot, item in assignments.items()
            if slot.day_index == day_index
        ]
        best: tuple[
            tuple[Decimal, Decimal, Decimal, Decimal, tuple[int, ...]],
            tuple[Recipe, ...],
        ] | None = None
        for selected in product(*choices):
            selected_assignments = [
                _assignment(slot, recipe, None)
                for slot, recipe in zip(empty_slots, selected)
            ]
            nutrients = _sum_nutrients([*fixed, *selected_assignments], nutrition)
            score = (
                *_nutrition_score(nutrients, targets),
                tuple(recipe.id for recipe in selected),
            )
            if best is None or score < best[0]:
                best = (score, selected)
        if best is None:
            continue
        for slot, recipe in zip(empty_slots, best[1]):
            assignments[slot] = _assignment(slot, recipe, None)
    return assignments


def _plan_score(
    assignments: dict[MealSlot, MealAssignment],
    nutrition: dict[int, Nutrients],
    targets: NutritionTargets,
) -> Score:
    totals = [Decimal(0), Decimal(0), Decimal(0), Decimal(0)]
    for day_index in range(7):
        day = _sum_nutrients(
            [
                assignment
                for slot, assignment in assignments.items()
                if slot.day_index == day_index
            ],
            nutrition,
        )
        for index, value in enumerate(_nutrition_score(day, targets)):
            totals[index] += value
    cooking_events = sum(
        1 for assignment in assignments.values() if assignment.recipe.servings == 1
    ) + sum(
        1
        for assignment in assignments.values()
        if assignment.portion_number == 1
    )
    ordered_slots = sorted(assignments, key=_slot_key)
    recipe_ids = tuple(assignments[slot].recipe.id for slot in ordered_slots)
    return (
        totals[0],
        totals[1],
        totals[2],
        totals[3],
        cooking_events,
        recipe_ids,
    )


def _nutrition_score(
    nutrients: Nutrients, targets: NutritionTargets
) -> tuple[Decimal, Decimal, Decimal, Decimal]:
    return (
        max(Decimal(0), targets.protein_minimum_g - nutrients.protein_g),
        max(Decimal(0), nutrients.calories_kcal - targets.calories_maximum_kcal),
        max(Decimal(0), nutrients.fat_g - targets.fat_maximum_g),
        abs(nutrients.carbohydrates_g - targets.carbohydrates_target_g),
    )


def _sum_nutrients(
    assignments: list[MealAssignment], nutrition: dict[int, Nutrients]
) -> Nutrients:
    total = Nutrients()
    for assignment in assignments:
        total += nutrition[assignment.recipe.id]
    return total


def _meal_slots(snacks_per_day: int) -> list[MealSlot]:
    slots: list[MealSlot] = []
    for day_index in range(7):
        slots.extend(MealSlot(day_index, role, 1) for role in MEAL_ROLES)
        slots.extend(
            MealSlot(day_index, "snack", slot_number)
            for slot_number in range(1, snacks_per_day + 1)
        )
    return slots


def _assignment(
    slot: MealSlot, recipe: Recipe, portion_number: int | None
) -> MealAssignment:
    return MealAssignment(
        day_index=slot.day_index,
        meal_role=slot.meal_role,
        slot_number=slot.slot_number,
        recipe=recipe,
        portion_number=portion_number,
    )


def _slot_key(slot: MealSlot) -> tuple[int, int, int]:
    return (
        slot.day_index,
        (*MEAL_ROLES, "snack").index(slot.meal_role),
        slot.slot_number,
    )


def slot_label(slot: MealSlot) -> str:
    role = {
        "breakfast": "Frühstück",
        "lunch": "Mittagessen",
        "dinner": "Abendessen",
        "snack": f"Snack {slot.slot_number}",
    }[slot.meal_role]
    return f"Tag {slot.day_index + 1}, {role}"
