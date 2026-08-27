from decimal import Decimal

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from preppilot_api.food_data_central import (
    FdcFoodPortion,
    FoodDetails,
    FoodNutrients,
    FoodSearchCandidate,
)
from preppilot_api.food_resolution import (
    AmbiguousFoodError,
    CatalogFoodDefinition,
    CatalogPortionDefinition,
    FoodResolutionError,
    FoodResolver,
)
from preppilot_api.models import Base, Food, FoodAlias, FoodPortion, MeasurementUnit


class StubFoodDataSource:
    def __init__(
        self,
        candidates: list[FoodSearchCandidate],
        details: FoodDetails,
        expected_query: str = "chicken breast",
    ) -> None:
        self.candidates = candidates
        self.details = details
        self.expected_query = expected_query
        self.search_calls = 0
        self.detail_calls = 0

    def search_foods(self, query: str) -> list[FoodSearchCandidate]:
        assert query == self.expected_query
        self.search_calls += 1
        return self.candidates

    def get_food(self, fdc_id: int) -> FoodDetails:
        assert fdc_id == self.details.fdc_id
        self.detail_calls += 1
        return self.details


def test_resolves_new_food_and_remembers_source_alias() -> None:
    data_source = StubFoodDataSource(
        candidates=[
            _candidate(
                2646170,
                "Chicken, breast, boneless, skinless, raw",
                "Foundation",
            ),
            _candidate(2727569, "Chicken, breast, meat and skin, raw", "Foundation"),
            _candidate(171477, "Chicken, breast, meat only, cooked", "SR Legacy"),
        ],
        details=_chicken_details(),
    )
    resolver = FoodResolver(data_source)

    with _session() as session:
        food = resolver.resolve(session, "TheMealDB", "  Chicken Breast ")
        session.commit()

        stored_alias = session.scalar(select(FoodAlias))
        assert stored_alias is not None
        assert stored_alias.source_name == "themealdb"
        assert stored_alias.external_name == "Chicken Breast"
        assert stored_alias.normalized_name == "chicken breast"
        assert stored_alias.food_id == food.id
        assert food.source_reference == "2646170"

        same_food = resolver.resolve(session, "themealdb", "CHICKEN  BREAST")
        assert same_food.id == food.id

    assert data_source.search_calls == 1
    assert data_source.detail_calls == 1


def test_rejects_candidates_with_an_equal_best_score() -> None:
    data_source = StubFoodDataSource(
        candidates=[
            _candidate(1, "Chicken breast, raw", "Foundation"),
            _candidate(2, "Chicken, breast, raw", "Foundation"),
        ],
        details=_chicken_details(),
    )
    resolver = FoodResolver(data_source)

    with _session() as session, pytest.raises(AmbiguousFoodError):
        resolver.resolve(session, "themealdb", "Chicken Breast")

    assert data_source.detail_calls == 0


def test_uses_source_specific_preference_for_known_ambiguity() -> None:
    base_details = _chicken_details()
    details = FoodDetails(
        fdc_id=base_details.fdc_id,
        description=base_details.description,
        data_type=base_details.data_type,
        nutrients_per_100g=base_details.nutrients_per_100g,
        portions=(
            FdcFoodPortion(
                source_id=12345,
                amount=Decimal("1"),
                gram_weight=Decimal("114"),
                unit="racc",
                modifier=None,
            ),
        ),
    )
    data_source = StubFoodDataSource(candidates=[], details=details)
    resolver = FoodResolver(
        data_source,
        preferred_fdc_ids={("themealdb", "chicken breast"): details.fdc_id},
    )

    with _session() as session:
        food = resolver.resolve(session, "TheMealDB", "Chicken Breast")
        session.flush()

        assert food.source_reference == "2646170"
        stored_portion = session.scalar(select(FoodPortion))
        assert stored_portion is not None
        assert stored_portion.gram_weight == Decimal("114")
        assert stored_portion.source_reference == "12345"

    assert data_source.search_calls == 0
    assert data_source.detail_calls == 1


def test_matches_plural_query_and_prefers_generic_raw_food() -> None:
    details = FoodDetails(
        fdc_id=170000,
        description="Onions, raw",
        data_type="SR Legacy",
        nutrients_per_100g=_chicken_details().nutrients_per_100g,
    )
    data_source = StubFoodDataSource(
        candidates=[
            _candidate(170000, "Onions, raw", "SR Legacy"),
            _candidate(790577, "Onions, red, raw", "Foundation"),
            _candidate(1104962, "Onions, white, raw", "Foundation"),
            _candidate(171327, "Spices, onion powder", "SR Legacy"),
        ],
        details=details,
        expected_query="onion",
    )

    with _session() as session:
        food = FoodResolver(data_source).resolve(session, "themealdb", "Onion")

        assert food.source_reference == "170000"


def test_uses_local_catalog_food_when_external_source_has_no_match() -> None:
    data_source = StubFoodDataSource(candidates=[], details=_chicken_details())
    resolver = FoodResolver(
        data_source,
        catalog_foods={
            ("themealdb", "harissa spice"): CatalogFoodDefinition(
                name="Harissa spice",
                unit=MeasurementUnit.GRAM,
                calories_per_100=Decimal("334"),
                protein_per_100=Decimal("14"),
                carbs_per_100=Decimal("36"),
                fat_per_100=Decimal("9.4"),
                source_name="test-source",
                source_reference="test-reference",
            )
        },
    )

    with _session() as session:
        food = resolver.resolve(session, "TheMealDB", "Harissa Spice")

        assert food.calories_per_100 == Decimal("334")
        assert food.source_name == "test-source"

    assert data_source.search_calls == 0
    assert data_source.detail_calls == 0


def test_adds_catalog_portion_to_new_and_existing_food_alias() -> None:
    data_source = StubFoodDataSource(
        candidates=[_candidate(2646170, "Chicken breast, raw", "Foundation")],
        details=_chicken_details(),
    )
    portion = CatalogPortionDefinition(
        amount=Decimal("1"),
        unit="handful",
        modifier=None,
        gram_weight=Decimal("10"),
        source_name="test-estimate",
        source_reference=None,
    )
    resolver = FoodResolver(
        data_source,
        catalog_portions={("themealdb", "chicken breast"): (portion,)},
    )

    with _session() as session:
        food = resolver.resolve(session, "themealdb", "Chicken Breast")
        resolver.resolve(session, "themealdb", "Chicken Breast")
        session.flush()

        stored = list(
            session.scalars(select(FoodPortion).where(FoodPortion.food_id == food.id))
        )
        assert len(stored) == 1
        assert stored[0].unit == "handful"
        assert stored[0].gram_weight == Decimal("10")


def test_does_not_treat_whole_food_as_flour() -> None:
    data_source = StubFoodDataSource(
        candidates=[_candidate(174288, "Chickpea flour (besan)", "SR Legacy")],
        details=_chicken_details(),
        expected_query="chickpeas",
    )

    with _session() as session, pytest.raises(FoodResolutionError):
        FoodResolver(data_source).resolve(session, "themealdb", "Chickpeas")

    assert data_source.detail_calls == 0


def test_does_not_persist_food_when_mvp_nutrients_are_incomplete() -> None:
    details = _chicken_details()
    incomplete_details = FoodDetails(
        fdc_id=details.fdc_id,
        description=details.description,
        data_type=details.data_type,
        nutrients_per_100g=FoodNutrients(
            calories=details.nutrients_per_100g.calories,
            protein=details.nutrients_per_100g.protein,
            carbs=None,
            fat=details.nutrients_per_100g.fat,
        ),
    )
    data_source = StubFoodDataSource(
        candidates=[
            _candidate(
                2646170,
                "Chicken, breast, boneless, skinless, raw",
                "Foundation",
            )
        ],
        details=incomplete_details,
    )
    resolver = FoodResolver(data_source)

    with _session() as session:
        with pytest.raises(ValueError):
            resolver.resolve(session, "themealdb", "Chicken Breast")

        assert session.scalar(select(Food)) is None


def _session() -> Session:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    return Session(engine)


def _candidate(fdc_id: int, description: str, data_type: str) -> FoodSearchCandidate:
    return FoodSearchCandidate(
        fdc_id=fdc_id,
        description=description,
        data_type=data_type,
    )


def _chicken_details() -> FoodDetails:
    return FoodDetails(
        fdc_id=2646170,
        description="Chicken, breast, boneless, skinless, raw",
        data_type="Foundation",
        nutrients_per_100g=FoodNutrients(
            calories=Decimal("106.034"),
            protein=Decimal("22.525"),
            carbs=Decimal("0"),
            fat=Decimal("1.934"),
        ),
    )
