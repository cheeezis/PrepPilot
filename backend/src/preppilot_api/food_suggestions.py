from dataclasses import dataclass
from enum import StrEnum

from preppilot_api.food_sources import FoodSearchCandidate
from preppilot_api.recipe_imports import normalize_text


class FoodSuggestionStatus(StrEnum):
    SELECTED = "selected"
    AMBIGUOUS = "ambiguous"
    NO_MATCH = "no_match"


@dataclass(frozen=True)
class RankedFoodCandidate:
    external_id: str
    name: str
    data_type: str
    score: int


@dataclass(frozen=True)
class FoodSuggestion:
    ingredient_name: str
    normalized_name: str
    status: FoodSuggestionStatus
    candidates: tuple[RankedFoodCandidate, ...]
    selected_external_id: str | None


@dataclass(frozen=True)
class LocalFoodCandidate:
    food_id: int
    catalog_key: str
    name: str


@dataclass(frozen=True)
class RankedLocalFoodCandidate:
    food_id: int
    catalog_key: str
    score: int


_IGNORED_QUALIFIERS = {
    "fresh",
    "raw",
    "cooked",
    "dried",
    "ground",
    "spice",
    "spices",
}
_SAFE_LOCAL_SUFFIXES = {"cheese", "leaf"}
_MINIMUM_SELECTION_SCORE = 90
_MINIMUM_SCORE_GAP = 10


def suggest_food(
    ingredient_name: str,
    candidates: tuple[FoodSearchCandidate, ...],
) -> FoodSuggestion:
    ranked = tuple(
        sorted(
            (
                RankedFoodCandidate(
                    external_id=candidate.external_id,
                    name=candidate.name,
                    data_type=candidate.data_type,
                    score=_score(ingredient_name, candidate.name),
                )
                for candidate in candidates
            ),
            key=lambda candidate: (-candidate.score, candidate.external_id),
        )
    )
    selected_external_id: str | None = None
    if not ranked:
        status = FoodSuggestionStatus.NO_MATCH
    else:
        second_score = ranked[1].score if len(ranked) > 1 else 0
        if (
            ranked[0].score >= _MINIMUM_SELECTION_SCORE
            and ranked[0].score - second_score >= _MINIMUM_SCORE_GAP
        ):
            status = FoodSuggestionStatus.SELECTED
            selected_external_id = ranked[0].external_id
        else:
            status = FoodSuggestionStatus.AMBIGUOUS

    return FoodSuggestion(
        ingredient_name=ingredient_name,
        normalized_name=normalize_text(ingredient_name),
        status=status,
        candidates=ranked,
        selected_external_id=selected_external_id,
    )


def suggest_local_food(
    ingredient_name: str,
    candidates: tuple[LocalFoodCandidate, ...],
) -> RankedLocalFoodCandidate | None:
    ranked = sorted(
        (
            RankedLocalFoodCandidate(
                food_id=candidate.food_id,
                catalog_key=candidate.catalog_key,
                score=max(
                    _local_score(ingredient_name, candidate.name),
                    _local_score(ingredient_name, candidate.catalog_key),
                ),
            )
            for candidate in candidates
        ),
        key=lambda candidate: (-candidate.score, candidate.food_id),
    )
    if not ranked:
        return None
    second_score = ranked[1].score if len(ranked) > 1 else 0
    if (
        ranked[0].score >= _MINIMUM_SELECTION_SCORE
        and ranked[0].score - second_score >= _MINIMUM_SCORE_GAP
    ):
        return ranked[0]
    return None


def _score(ingredient_name: str, candidate_name: str) -> int:
    ingredient = normalize_text(ingredient_name)
    candidate = normalize_text(candidate_name)
    if ingredient == candidate:
        return 100

    ingredient_core = _core(ingredient)
    candidate_core = _core(candidate)
    if ingredient_core and ingredient_core == candidate_core:
        return 95
    if candidate_core.startswith(f"{ingredient_core} "):
        return 85

    ingredient_tokens = set(ingredient_core.split())
    candidate_tokens = set(candidate_core.split())
    if ingredient_tokens and ingredient_tokens <= candidate_tokens:
        return 80
    if not ingredient_tokens or not candidate_tokens:
        return 0
    overlap = len(ingredient_tokens & candidate_tokens)
    return round(70 * overlap / len(ingredient_tokens | candidate_tokens))


def _local_score(ingredient_name: str, candidate_name: str) -> int:
    score = _score(ingredient_name, candidate_name)
    ingredient_core = _core(normalize_text(ingredient_name))
    candidate_core = _core(normalize_text(candidate_name))
    if candidate_core and ingredient_core.startswith(f"{candidate_core} "):
        suffix = set(ingredient_core.removeprefix(candidate_core).split())
        if suffix and suffix <= _SAFE_LOCAL_SUFFIXES:
            return max(score, 90)
    return score


def _core(value: str) -> str:
    return " ".join(
        _singular(token)
        for token in value.split()
        if token not in _IGNORED_QUALIFIERS
    )


def _singular(token: str) -> str:
    if len(token) > 4 and token.endswith("ies"):
        return f"{token[:-3]}y"
    if len(token) > 3 and token.endswith("s") and not token.endswith("ss"):
        return token[:-1]
    return token
