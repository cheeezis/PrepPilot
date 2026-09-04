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

def _add_optional(left: Decimal | None, right: Decimal | None) -> Decimal | None:
    return None if left is None or right is None else left + right
