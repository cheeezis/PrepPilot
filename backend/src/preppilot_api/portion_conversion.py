from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable, Protocol

from preppilot_api.measurements import ParsedMeasurement
from preppilot_api.models import MeasurementUnit


class UnsupportedPortionError(ValueError):
    pass


class Portion(Protocol):
    amount: Decimal
    unit: str
    modifier: str | None
    gram_weight: Decimal


@dataclass(frozen=True)
class ConvertedMeasurement:
    amount: Decimal
    unit: MeasurementUnit


_VOLUME_IN_MILLILITERS = {
    "tsp": Decimal("5"),
    "tbsp": Decimal("15"),
    "cup": Decimal("240"),
}


def convert_measurement(
    measurement: ParsedMeasurement,
    target_unit: MeasurementUnit,
    portions: Iterable[Portion] = (),
) -> ConvertedMeasurement:
    available_portions = tuple(portions)

    if measurement.unit == target_unit.value:
        return ConvertedMeasurement(measurement.amount, target_unit)

    if target_unit == MeasurementUnit.MILLILITER:
        volume = _VOLUME_IN_MILLILITERS.get(measurement.unit)
        if volume is not None:
            return ConvertedMeasurement(measurement.amount * volume, target_unit)

    if target_unit == MeasurementUnit.GRAM:
        portion = _select_portion(measurement, available_portions)
        if portion is not None:
            return ConvertedMeasurement(
                measurement.amount * portion.gram_weight / portion.amount,
                target_unit,
            )
        if measurement.unit == "ml":
            density = _density_from_volume_portion(available_portions)
            if density is not None:
                return ConvertedMeasurement(measurement.amount * density, target_unit)

    raise UnsupportedPortionError(
        f"Cannot convert {measurement.amount} {measurement.unit} to {target_unit.value}"
    )


def _select_portion(
    measurement: ParsedMeasurement, portions: tuple[Portion, ...]
) -> Portion | None:
    candidates = [portion for portion in portions if portion.unit == measurement.unit]
    if not candidates:
        return None

    if measurement.modifier is not None:
        exact = [
            portion
            for portion in candidates
            if portion.modifier is not None
            and portion.modifier.casefold() == measurement.modifier.casefold()
        ]
        if exact:
            return exact[0]

    medium = [portion for portion in candidates if portion.modifier == "medium"]
    if medium:
        return medium[0]
    unmodified = [portion for portion in candidates if portion.modifier is None]
    if unmodified:
        return unmodified[0]
    if len(candidates) == 1:
        return candidates[0]
    return None


def _density_from_volume_portion(portions: tuple[Portion, ...]) -> Decimal | None:
    for unit in ("cup", "tbsp", "tsp"):
        for portion in portions:
            if portion.unit == unit:
                volume = portion.amount * _VOLUME_IN_MILLILITERS[unit]
                return portion.gram_weight / volume
    return None
