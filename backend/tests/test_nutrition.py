from decimal import Decimal

from preppilot_api.nutrition import Nutrients


def test_scales_source_nutrients_by_whole_portions() -> None:
    nutrients = Nutrients(Decimal("525"), Decimal("52"), Decimal("48"), Decimal("15.5"))
    assert nutrients.scaled(2) == Nutrients(
        Decimal("1050"), Decimal("104"), Decimal("96"), Decimal("31.0")
    )
