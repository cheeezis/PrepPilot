from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Nutrients:
    calories: Decimal = Decimal(0)
    protein: Decimal = Decimal(0)
    carbs: Decimal = Decimal(0)
    fat: Decimal = Decimal(0)
    sugar: Decimal | None = Decimal(0)
    saturated_fat: Decimal | None = Decimal(0)
    fiber: Decimal | None = Decimal(0)
    salt: Decimal | None = Decimal(0)

    def __add__(self, other: "Nutrients") -> "Nutrients":
        return Nutrients(
            calories=self.calories + other.calories,
            protein=self.protein + other.protein,
            carbs=self.carbs + other.carbs,
            fat=self.fat + other.fat,
            sugar=_add_optional(self.sugar, other.sugar),
            saturated_fat=_add_optional(self.saturated_fat, other.saturated_fat),
            fiber=_add_optional(self.fiber, other.fiber),
            salt=_add_optional(self.salt, other.salt),
        )

    def scaled(self, factor: int) -> "Nutrients":
        scale = Decimal(factor)
        return Nutrients(
            calories=self.calories * scale,
            protein=self.protein * scale,
            carbs=self.carbs * scale,
            fat=self.fat * scale,
            sugar=_scale_optional(self.sugar, scale),
            saturated_fat=_scale_optional(self.saturated_fat, scale),
            fiber=_scale_optional(self.fiber, scale),
            salt=_scale_optional(self.salt, scale),
        )


def _add_optional(left: Decimal | None, right: Decimal | None) -> Decimal | None:
    return None if left is None or right is None else left + right


def _scale_optional(value: Decimal | None, scale: Decimal) -> Decimal | None:
    return None if value is None else value * scale
