from dataclasses import dataclass
from enum import StrEnum

from sqlalchemy.orm import Session

from preppilot_api.models import (
    ImportReviewReason,
    RecipeImport,
    RecipeImportStatus,
)
from preppilot_api.recipe_imports import ingredients_for_import


class ReviewPriority(StrEnum):
    READY = "ready"
    LOW_EFFORT = "low_effort"
    MEDIUM_EFFORT = "medium_effort"
    HIGH_EFFORT = "high_effort"
    LOW_QUALITY = "low_quality"
    REJECTED = "rejected"


@dataclass(frozen=True)
class RecipeImportAssessment:
    score: int
    priority: ReviewPriority
    issues: tuple[str, ...]
    unknown_ingredient_count: int
    review_item_count: int


_PRIORITY_ORDER = {
    ReviewPriority.READY: 0,
    ReviewPriority.LOW_EFFORT: 1,
    ReviewPriority.MEDIUM_EFFORT: 2,
    ReviewPriority.HIGH_EFFORT: 3,
    ReviewPriority.LOW_QUALITY: 4,
    ReviewPriority.REJECTED: 5,
}


def assess_recipe_import(
    session: Session, recipe_import: RecipeImport
) -> RecipeImportAssessment:
    ingredients = ingredients_for_import(session, recipe_import.id)
    reasons = [
        ingredient.review_reason
        for ingredient in ingredients
        if ingredient.review_reason is not None
    ]
    unknown_count = reasons.count(ImportReviewReason.UNKNOWN_FOOD)
    non_serving_review_count = sum(
        reason != ImportReviewReason.MISSING_SERVING_COUNT for reason in reasons
    )
    missing_servings = (
        recipe_import.manual_servings is None and recipe_import.raw_servings is None
    )
    instructions = _instructions(recipe_import.raw_payload)
    insufficient_instructions = len(" ".join(instructions.split())) < 80

    issues: list[str] = []
    if missing_servings:
        issues.append("missing_serving_count")
    if insufficient_instructions:
        issues.append("insufficient_instructions")
    if unknown_count:
        issues.append("unknown_foods")
    if non_serving_review_count > unknown_count:
        issues.append("unresolved_measures")

    score = 100
    score -= 30 if missing_servings else 0
    score -= 30 if insufficient_instructions else 0
    score -= min(30, unknown_count * 6)
    score -= min(20, (non_serving_review_count - unknown_count) * 4)
    score = max(0, score)

    effort = non_serving_review_count + int(missing_servings)
    if recipe_import.status == RecipeImportStatus.REJECTED:
        priority = ReviewPriority.REJECTED
    elif insufficient_instructions:
        priority = ReviewPriority.LOW_QUALITY
    elif recipe_import.status == RecipeImportStatus.READY_FOR_CATALOG_REVIEW:
        priority = ReviewPriority.READY
    elif effort <= 3:
        priority = ReviewPriority.LOW_EFFORT
    elif effort <= 7:
        priority = ReviewPriority.MEDIUM_EFFORT
    else:
        priority = ReviewPriority.HIGH_EFFORT

    return RecipeImportAssessment(
        score=score,
        priority=priority,
        issues=tuple(issues),
        unknown_ingredient_count=unknown_count,
        review_item_count=effort,
    )


def assessment_sort_key(
    assessment: RecipeImportAssessment,
) -> tuple[int, int, int]:
    return (
        _PRIORITY_ORDER[assessment.priority],
        assessment.review_item_count,
        -assessment.score,
    )


def _instructions(raw_payload: dict[str, object]) -> str:
    for key in ("strInstructions", "instructions"):
        value = raw_payload.get(key)
        if isinstance(value, str):
            return value.strip()
    return ""
