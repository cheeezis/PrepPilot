from decimal import Decimal

import pytest

from preppilot_api.measurements import (
    ParsedMeasurement,
    UnsupportedMeasurementError,
    parse_measurement,
)


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("1 pound", ParsedMeasurement(Decimal("500"), "g")),
        ("2 x 400g", ParsedMeasurement(Decimal("800"), "g")),
        ("1/4 cup", ParsedMeasurement(Decimal("0.25"), "cup")),
        ("1 1/2 tbsp", ParsedMeasurement(Decimal("1.5"), "tbsp")),
        ("½ teaspoon", ParsedMeasurement(Decimal("0.5"), "tsp")),
        ("3 cloves", ParsedMeasurement(Decimal("3"), "piece", "clove")),
        ("1 chopped", ParsedMeasurement(Decimal("1"), "piece", "chopped")),
        ("10", ParsedMeasurement(Decimal("10"), "piece")),
        ("Handful", ParsedMeasurement(Decimal("1"), "handful")),
        ("for frying", ParsedMeasurement(Decimal("1"), "for_frying")),
    ],
)
def test_parses_measurement_without_food_knowledge(
    source: str, expected: ParsedMeasurement
) -> None:
    assert parse_measurement(source) == expected


def test_rejects_unknown_measurement() -> None:
    with pytest.raises(UnsupportedMeasurementError):
        parse_measurement("to taste")
