from decimal import Decimal

from preppilot_api.catalog_data import load_catalog_configuration


def test_loads_structured_catalog_overrides() -> None:
    catalog = load_catalog_configuration()

    assert catalog.preferred_fdc_ids[("themealdb", "chickpeas")] == 2644288
    assert catalog.foods[("themealdb", "harissa spice")].protein_per_100 == Decimal(
        "14"
    )
    assert catalog.portions[("themealdb", "coriander")][0].unit == "handful"
    assert catalog.portions[("themealdb", "coriander")][0].gram_weight == Decimal("10")
