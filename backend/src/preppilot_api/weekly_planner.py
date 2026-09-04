from dataclasses import dataclass

from preppilot_api.models import MealAssignment, Recipe

MEAL_ROLES = ("breakfast", "lunch", "dinner")


class PlanGenerationError(Exception):
    pass


@dataclass(frozen=True)
class MealSlot:
    day_index: int
    meal_role: str
    slot_number: int


def generate_assignments(
    recipes: list[Recipe], snacks_per_day: int
) -> list[MealAssignment]:
    slots = _meal_slots(snacks_per_day)
    assignments: dict[MealSlot, MealAssignment] = {}

    batch_recipes = sorted(
        (recipe for recipe in recipes if recipe.servings > 1),
        key=lambda recipe: recipe.id,
    )
    for recipe in batch_recipes:
        roles = {item.meal_role for item in recipe.meal_roles}
        compatible_slots = [
            slot
            for slot in slots
            if slot not in assignments and slot.meal_role in roles
        ]
        if len(compatible_slots) < recipe.servings:
            continue
        for portion_number, slot in enumerate(
            compatible_slots[: recipe.servings], start=1
        ):
            assignments[slot] = _assignment(slot, recipe, portion_number)

    single_recipes = [recipe for recipe in recipes if recipe.servings == 1]
    role_offsets: dict[str, int] = {}
    for slot in slots:
        if slot in assignments:
            continue
        compatible_recipes = [
            recipe
            for recipe in single_recipes
            if slot.meal_role in {item.meal_role for item in recipe.meal_roles}
        ]
        if not compatible_recipes:
            raise PlanGenerationError(
                f"Kein Einzelrezept für {slot_label(slot)} verfügbar"
            )
        offset = role_offsets.get(slot.meal_role, 0)
        recipe = compatible_recipes[offset % len(compatible_recipes)]
        role_offsets[slot.meal_role] = offset + 1
        assignments[slot] = _assignment(slot, recipe, None)

    return [assignments[slot] for slot in slots]


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


def slot_label(slot: MealSlot) -> str:
    role = {
        "breakfast": "Frühstück",
        "lunch": "Mittagessen",
        "dinner": "Abendessen",
        "snack": f"Snack {slot.slot_number}",
    }[slot.meal_role]
    return f"Tag {slot.day_index + 1}, {role}"
