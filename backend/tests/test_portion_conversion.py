from dataclasses import dataclass
from decimal import Decimal

import pytest

from preppilot_api.measurements import ParsedMeasurement
from preppilot_api.models import MeasurementUnit
from preppilot_api.portion_conversion import (
    ConvertedMeasurement,
    UnsupportedPortionError,
    convert_measurement,
)


@dataclass(frozen=True)
class StubPortion:
    amount: Decimal
    unit: str
    gram_weight: Decimal
    modifier: str | None = None


def test_keeps_measurement_already_in_food_unit() -> None:
    result = convert_measurement(
        ParsedMeasurement(Decimal("200"), "g"),
        MeasurementUnit.GRAM,
    )

    assert result == ConvertedMeasurement(Decimal("200"), MeasurementUnit.GRAM)


def test_uses_matching_food_portion() -> None:
    result = convert_measurement(
        ParsedMeasurement(Decimal("2"), "tbsp"),
        MeasurementUnit.GRAM,
        [StubPortion(Decimal("1"), "tbsp", Decimal("13.5"))],
    )

    assert result.amount == Decimal("27.0")


def test_prefers_exact_piece_modifier_then_medium_fallback() -> None:
    portions = [
        StubPortion(Decimal("1"), "piece", Decimal("70"), "small"),
        StubPortion(Decimal("1"), "piece", Decimal("110"), "medium"),
        StubPortion(Decimal("1"), "piece", Decimal("150"), "large"),
    ]

    exact = convert_measurement(
        ParsedMeasurement(Decimal("2"), "piece", "small"),
        MeasurementUnit.GRAM,
        portions,
    )
    fallback = convert_measurement(
        ParsedMeasurement(Decimal("1"), "piece", "chopped"),
        MeasurementUnit.GRAM,
        portions,
    )

    assert exact.amount == Decimal("140")
    assert fallback.amount == Decimal("110")


def test_scales_fractional_source_portion() -> None:
    result = convert_measurement(
        ParsedMeasurement(Decimal("10"), "piece"),
        MeasurementUnit.GRAM,
        [StubPortion(Decimal("0.5"), "piece", Decimal("3.5"))],
    )

    assert result.amount == Decimal("70")


def test_derives_simple_density_from_volume_portion() -> None:
    result = convert_measurement(
        ParsedMeasurement(Decimal("200"), "ml"),
        MeasurementUnit.GRAM,
        [StubPortion(Decimal("1"), "cup", Decimal("240"))],
    )

    assert result.amount == Decimal("200")


def test_converts_household_volume_for_milliliter_food() -> None:
    result = convert_measurement(
        ParsedMeasurement(Decimal("1.5"), "tbsp"),
        MeasurementUnit.MILLILITER,
    )

    assert result.amount == Decimal("22.5")


def test_rejects_measurement_without_usable_portion() -> None:
    with pytest.raises(UnsupportedPortionError):
        convert_measurement(
            ParsedMeasurement(Decimal("1"), "handful"),
            MeasurementUnit.GRAM,
        )
