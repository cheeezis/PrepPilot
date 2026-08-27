import re
from dataclasses import dataclass
from decimal import Decimal


class UnsupportedMeasurementError(ValueError):
    pass


@dataclass(frozen=True)
class ParsedMeasurement:
    amount: Decimal
    unit: str
    modifier: str | None = None


_QUANTITY_PATTERN = r"(?:\d+(?:[.,]\d+)?(?:\s+\d+/\d+)?|\d+/\d+)"
_MULTIPLIED_MEASUREMENT = re.compile(
    rf"^(?P<count>{_QUANTITY_PATTERN})\s*x\s*"
    rf"(?P<amount>{_QUANTITY_PATTERN})\s*(?P<unit>[a-z]+)\b"
)
_STANDARD_MEASUREMENT = re.compile(
    rf"^(?P<amount>{_QUANTITY_PATTERN})\s*(?P<unit>[a-z]+)\b"
)
_LEADING_QUANTITY = re.compile(
    rf"^(?P<amount>{_QUANTITY_PATTERN})(?:\s+(?P<description>.*))?$"
)

_UNICODE_FRACTIONS = {
    "¼": "1/4",
    "½": "1/2",
    "¾": "3/4",
    "⅓": "1/3",
    "⅔": "2/3",
    "⅛": "1/8",
}

_UNIT_ALIASES: dict[str, tuple[str, Decimal]] = {
    "g": ("g", Decimal("1")),
    "gram": ("g", Decimal("1")),
    "grams": ("g", Decimal("1")),
    "kg": ("g", Decimal("1000")),
    "oz": ("g", Decimal("30")),
    "ounce": ("g", Decimal("30")),
    "ounces": ("g", Decimal("30")),
    "lb": ("g", Decimal("500")),
    "lbs": ("g", Decimal("500")),
    "pound": ("g", Decimal("500")),
    "pounds": ("g", Decimal("500")),
    "ml": ("ml", Decimal("1")),
    "l": ("ml", Decimal("1000")),
    "liter": ("ml", Decimal("1000")),
    "liters": ("ml", Decimal("1000")),
    "litre": ("ml", Decimal("1000")),
    "litres": ("ml", Decimal("1000")),
    "tsp": ("tsp", Decimal("1")),
    "teaspoon": ("tsp", Decimal("1")),
    "teaspoons": ("tsp", Decimal("1")),
    "tbsp": ("tbsp", Decimal("1")),
    "tbs": ("tbsp", Decimal("1")),
    "tblsp": ("tbsp", Decimal("1")),
    "tablespoon": ("tbsp", Decimal("1")),
    "tablespoons": ("tbsp", Decimal("1")),
    "cup": ("cup", Decimal("1")),
    "cups": ("cup", Decimal("1")),
    "tin": ("tin", Decimal("1")),
    "tins": ("tin", Decimal("1")),
    "can": ("tin", Decimal("1")),
    "cans": ("tin", Decimal("1")),
    "clove": ("piece", Decimal("1")),
    "cloves": ("piece", Decimal("1")),
    "sprig": ("sprig", Decimal("1")),
    "sprigs": ("sprig", Decimal("1")),
    "slice": ("slice", Decimal("1")),
    "slices": ("slice", Decimal("1")),
}

_DESCRIPTIVE_UNITS = {
    "dash": "dash",
    "handful": "handful",
    "pinch": "pinch",
    "sprinkling": "sprinkling",
    "splash": "splash",
}


def parse_measurement(value: str) -> ParsedMeasurement:
    normalized = _normalize_text(value)

    multiplied = _MULTIPLIED_MEASUREMENT.match(normalized)
    if multiplied and multiplied.group("unit") in _UNIT_ALIASES:
        return _measurement_from_unit(
            _parse_quantity(multiplied.group("count"))
            * _parse_quantity(multiplied.group("amount")),
            multiplied.group("unit"),
        )

    standard = _STANDARD_MEASUREMENT.match(normalized)
    if standard and standard.group("unit") in _UNIT_ALIASES:
        return _measurement_from_unit(
            _parse_quantity(standard.group("amount")),
            standard.group("unit"),
        )

    quantity = _LEADING_QUANTITY.match(normalized)
    if quantity:
        return ParsedMeasurement(
            amount=_parse_quantity(quantity.group("amount")),
            unit="piece",
            modifier=quantity.group("description"),
        )

    if normalized in _DESCRIPTIVE_UNITS:
        return ParsedMeasurement(
            amount=Decimal("1"),
            unit=_DESCRIPTIVE_UNITS[normalized],
        )
    if normalized == "for frying":
        return ParsedMeasurement(amount=Decimal("1"), unit="for_frying")

    raise UnsupportedMeasurementError(f"Unsupported measurement {value!r}")


def _normalize_text(value: str) -> str:
    normalized = value.strip().lower().replace("×", "x")
    for fraction, replacement in _UNICODE_FRACTIONS.items():
        normalized = normalized.replace(fraction, f" {replacement}")
    return " ".join(normalized.split())


def _parse_quantity(value: str) -> Decimal:
    parts = value.replace(",", ".").split()
    total = Decimal("0")
    for part in parts:
        if "/" in part:
            numerator, denominator = part.split("/", maxsplit=1)
            total += Decimal(numerator) / Decimal(denominator)
        else:
            total += Decimal(part)
    return total


def _measurement_from_unit(amount: Decimal, source_unit: str) -> ParsedMeasurement:
    unit, factor = _UNIT_ALIASES[source_unit]
    modifier = "clove" if source_unit.startswith("clove") else None
    return ParsedMeasurement(amount=amount * factor, unit=unit, modifier=modifier)
