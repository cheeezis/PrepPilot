from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Nutrients:
    calories: Decimal = Decimal(0)
    protein: Decimal = Decimal(0)
    carbs: Decimal = Decimal(0)
    fat: Decimal = Decimal(0)

    def __add__(self, other: "Nutrients") -> "Nutrients":
        return Nutrients(
            calories=self.calories + other.calories,
            protein=self.protein + other.protein,
            carbs=self.carbs + other.carbs,
            fat=self.fat + other.fat,
        )

    def scaled(self, factor: int) -> "Nutrients":
        scale = Decimal(factor)
        return Nutrients(
            calories=self.calories * scale,
            protein=self.protein * scale,
            carbs=self.carbs * scale,
            fat=self.fat * scale,
        )
