from collections import Counter

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from preppilot_api.catalog_data import Catalog, load_catalog
from preppilot_api.database import engine
from preppilot_api.models import (
    Food,
    FoodAlias,
    FoodConcept,
    FoodMeasureDefault,
    FoodOrigin,
    FoodSourceIdentifier,
    Meal,
    MealIngredient,
    MealOrigin,
    MealPortionFactor,
    MealRoleAssignment,
    RecipeImportIngredient,
)
from preppilot_api.recipe_imports import canonical_measure, normalize_text

_CURATED_NORMALIZATION_SOURCE = "PrepPilot curated catalog"


def replace_catalog(session: Session, catalog: Catalog) -> None:
    existing_meals = {meal.catalog_key: meal for meal in session.scalars(select(Meal))}
    curated_meal_ids = {
        meal.id
        for meal in existing_meals.values()
        if meal.origin == MealOrigin.CURATED_SEED
    }
    if curated_meal_ids:
        session.execute(
            delete(MealRoleAssignment).where(
                MealRoleAssignment.meal_id.in_(curated_meal_ids)
            )
        )
        session.execute(
            delete(MealPortionFactor).where(
                MealPortionFactor.meal_id.in_(curated_meal_ids)
            )
        )
        session.execute(
            delete(MealIngredient).where(MealIngredient.meal_id.in_(curated_meal_ids))
        )

    existing_foods = {food.catalog_key: food for food in session.scalars(select(Food))}
    initial_concept_food_counts = Counter(
        food.concept_id for food in existing_foods.values()
    )
    concepts = {
        concept.key: concept for concept in session.scalars(select(FoodConcept))
    }
    foods: dict[str, Food] = {}
    for food_definition in catalog.foods:
        concept = concepts.get(food_definition.concept_key)
        if concept is None:
            concept = FoodConcept(
                key=food_definition.concept_key,
                name=food_definition.concept_name,
            )
            session.add(concept)
            session.flush()
            concepts[food_definition.concept_key] = concept
        else:
            concept.name = food_definition.concept_name

        legacy_concept = concepts.get(food_definition.key)
        if (
            legacy_concept is not None
            and legacy_concept.id != concept.id
            and initial_concept_food_counts[legacy_concept.id] <= 1
        ):
            _move_legacy_concept_references(
                session,
                old_concept_id=legacy_concept.id,
                new_concept_id=concept.id,
            )

        food = existing_foods.pop(food_definition.key, None)
        if food is not None and food.origin != FoodOrigin.CURATED_SEED:
            raise ValueError(
                f"Seed food key conflicts with imported food: {food.catalog_key}"
            )
        if food is None:
            food = Food(
                catalog_key=food_definition.key,
                concept_id=concept.id,
                origin=FoodOrigin.CURATED_SEED,
            )
            session.add(food)
        food.concept_id = concept.id
        food.name = food_definition.name
        food.brand = food_definition.brand
        food.unit = food_definition.unit
        food.calories_per_100 = food_definition.calories_per_100
        food.protein_per_100 = food_definition.protein_per_100
        food.carbs_per_100 = food_definition.carbs_per_100
        food.fat_per_100 = food_definition.fat_per_100
        food.source_name = food_definition.source_name
        food.source_reference = food_definition.source_reference
        foods[food_definition.key] = food

    for stale_food in existing_foods.values():
        if stale_food.origin == FoodOrigin.CURATED_SEED:
            session.delete(stale_food)

    session.flush()

    _replace_curated_normalization_metadata(session, catalog, foods)

    for meal_definition in catalog.meals:
        meal = existing_meals.pop(meal_definition.key, None)
        if meal is not None and meal.origin != MealOrigin.CURATED_SEED:
            raise ValueError(
                f"Seed meal key conflicts with imported meal: {meal.catalog_key}"
            )
        if meal is None:
            meal = Meal(
                catalog_key=meal_definition.key,
                origin=MealOrigin.CURATED_SEED,
                source_recipe_import_id=None,
            )
            session.add(meal)
        meal.name = meal_definition.name
        meal.preparation_minutes = meal_definition.preparation_minutes
        meal.instructions = meal_definition.instructions
        session.flush()
        session.add_all(
            MealIngredient(
                meal_id=meal.id,
                food_id=foods[ingredient.food_key].id,
                amount=ingredient.amount,
            )
            for ingredient in meal_definition.ingredients
        )
        session.add_all(
            MealRoleAssignment(meal_id=meal.id, role=role)
            for role in meal_definition.roles
        )
        session.add_all(
            MealPortionFactor(meal_id=meal.id, factor=factor)
            for factor in meal_definition.portion_factors
        )

    for stale_meal in existing_meals.values():
        if stale_meal.origin == MealOrigin.CURATED_SEED:
            session.delete(stale_meal)

    session.flush()
    _delete_unreferenced_concepts(session)


def _delete_unreferenced_concepts(session: Session) -> None:
    referenced_concept_ids = set(session.scalars(select(Food.concept_id)))
    referenced_concept_ids.update(
        concept_id
        for concept_id in session.scalars(select(FoodSourceIdentifier.concept_id))
        if concept_id is not None
    )
    referenced_concept_ids.update(
        concept_id
        for concept_id in session.scalars(select(RecipeImportIngredient.concept_id))
        if concept_id is not None
    )
    for concept in session.scalars(select(FoodConcept)):
        if concept.id not in referenced_concept_ids:
            session.delete(concept)


def _move_legacy_concept_references(
    session: Session,
    *,
    old_concept_id: int,
    new_concept_id: int,
) -> None:
    session.execute(
        update(FoodSourceIdentifier)
        .where(FoodSourceIdentifier.concept_id == old_concept_id)
        .values(concept_id=new_concept_id)
    )
    session.execute(
        update(RecipeImportIngredient)
        .where(RecipeImportIngredient.concept_id == old_concept_id)
        .values(concept_id=new_concept_id)
    )


def _replace_curated_normalization_metadata(
    session: Session,
    catalog: Catalog,
    foods: dict[str, Food],
) -> None:
    aliases = {
        alias.normalized_alias: alias for alias in session.scalars(select(FoodAlias))
    }
    desired_aliases: set[str] = set()
    defaults = {
        (default.food_id, default.measure_key): default
        for default in session.scalars(select(FoodMeasureDefault))
    }
    desired_defaults: set[tuple[int, str]] = set()

    for definition in catalog.foods:
        food = foods[definition.key]
        for alias_value in definition.aliases:
            normalized_alias = normalize_text(alias_value)
            desired_aliases.add(normalized_alias)
            alias = aliases.get(normalized_alias)
            if alias is not None and alias.food_id != food.id:
                raise ValueError(
                    f"Catalog alias conflicts with existing alias: {alias_value}"
                )
            if alias is None:
                session.add(
                    FoodAlias(
                        alias=alias_value,
                        normalized_alias=normalized_alias,
                        food_id=food.id,
                        source_name=_CURATED_NORMALIZATION_SOURCE,
                    )
                )

        for definition_default in definition.measure_defaults:
            measure_key = canonical_measure(definition_default.key)
            if measure_key is None:
                raise ValueError("Catalog measure key must not be blank")
            identity = (food.id, measure_key)
            desired_defaults.add(identity)
            default = defaults.get(identity)
            if default is not None and not default.source_name.startswith(
                _CURATED_NORMALIZATION_SOURCE
            ):
                if default.amount != definition_default.amount:
                    raise ValueError(
                        "Catalog measure default conflicts with reviewed default: "
                        f"{definition.key}/{measure_key}"
                    )
                continue
            if default is None:
                default = FoodMeasureDefault(food_id=food.id, measure_key=measure_key)
                session.add(default)
            default.amount = definition_default.amount
            default.source_name = (
                f"{_CURATED_NORMALIZATION_SOURCE}: {definition_default.source_name}"
            )
            default.source_reference = definition_default.source_reference

    for alias in aliases.values():
        if (
            alias.source_name == _CURATED_NORMALIZATION_SOURCE
            and alias.normalized_alias not in desired_aliases
        ):
            session.delete(alias)
    for identity, default in defaults.items():
        if (
            default.source_name.startswith(_CURATED_NORMALIZATION_SOURCE)
            and identity not in desired_defaults
        ):
            session.delete(default)


def main() -> None:
    catalog = load_catalog()
    with Session(engine) as session, session.begin():
        replace_catalog(session, catalog)
    print(f"Loaded {len(catalog.foods)} foods and {len(catalog.meals)} meals")


if __name__ == "__main__":
    main()
