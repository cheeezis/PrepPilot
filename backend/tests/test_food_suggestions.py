from preppilot_api.food_sources import FoodSearchCandidate
from preppilot_api.food_suggestions import (
    FoodSuggestionStatus,
    LocalFoodCandidate,
    suggest_food,
    suggest_local_food,
)


def test_suggestion_selects_unique_qualified_generic_match() -> None:
    suggestion = suggest_food(
        "Parsley",
        (
            FoodSearchCandidate("170416", "Parsley, fresh", "SR Legacy"),
            FoodSearchCandidate("170486", "Parsley, freeze-dried", "SR Legacy"),
        ),
    )

    assert suggestion.status == FoodSuggestionStatus.SELECTED
    assert suggestion.selected_external_id == "170416"
    assert [candidate.score for candidate in suggestion.candidates] == [95, 85]


def test_suggestion_keeps_broad_ingredient_ambiguous() -> None:
    suggestion = suggest_food(
        "Pepper",
        (
            FoodSearchCandidate("170931", "Spices, pepper, black", "SR Legacy"),
            FoodSearchCandidate("170108", "Peppers, sweet, red, raw", "SR Legacy"),
        ),
    )

    assert suggestion.status == FoodSuggestionStatus.AMBIGUOUS
    assert suggestion.selected_external_id is None
    assert suggestion.candidates[0].score == 85


def test_suggestion_reports_missing_candidates() -> None:
    suggestion = suggest_food("Unknown ingredient", ())

    assert suggestion.status == FoodSuggestionStatus.NO_MATCH
    assert not suggestion.candidates


def test_suggestion_does_not_confuse_plum_tomatoes_with_plums() -> None:
    suggestion = suggest_food(
        "Plum Tomatoes",
        (
            FoodSearchCandidate("169949", "Plums, raw", "SR Legacy"),
            FoodSearchCandidate(
                "170457", "Tomatoes, red, ripe, raw", "SR Legacy"
            ),
        ),
    )

    assert suggestion.status == FoodSuggestionStatus.AMBIGUOUS
    assert suggestion.selected_external_id is None


def test_local_suggestion_matches_safe_food_variant() -> None:
    suggestion = suggest_local_food(
        "Chickpeas",
        (
            LocalFoodCandidate(1, "chickpeas_cooked", "Chickpeas, cooked"),
            LocalFoodCandidate(2, "chicken_breast", "Chicken breast, raw"),
        ),
    )

    assert suggestion is not None
    assert suggestion.catalog_key == "chickpeas_cooked"
    assert suggestion.score == 90


def test_local_suggestion_does_not_collapse_broad_food_name() -> None:
    suggestion = suggest_local_food(
        "Chicken",
        (
            LocalFoodCandidate(1, "chicken_breast", "Chicken breast, raw"),
            LocalFoodCandidate(2, "chicken_thigh", "Chicken thigh, raw"),
        ),
    )

    assert suggestion is None


def test_local_suggestion_does_not_collapse_concentrated_food() -> None:
    suggestion = suggest_local_food(
        "Tomato Puree",
        (LocalFoodCandidate(1, "tomato", "Tomato"),),
    )

    assert suggestion is None


def test_processing_state_is_not_discarded_for_selection() -> None:
    dried = suggest_food(
        "Dried Apricots",
        (
            FoodSearchCandidate("1", "Apricots, raw", "SR Legacy"),
            FoodSearchCandidate("2", "Apricots, dried", "SR Legacy"),
        ),
    )
    ground = suggest_food(
        "Ground Onion",
        (FoodSearchCandidate("3", "Onions, raw", "SR Legacy"),),
    )

    assert dried.selected_external_id == "2"
    assert ground.status == FoodSuggestionStatus.AMBIGUOUS
    assert ground.selected_external_id is None
