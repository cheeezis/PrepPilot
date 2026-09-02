import csv
import io
import zipfile
from decimal import Decimal

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from preppilot_api.food_reference import (
    FoodReferenceDataset,
    import_food_references,
    parse_food_reference_archive,
)
from preppilot_api.models import Base, FoodReferenceItem


def test_parses_and_imports_fdc_csv_archive_idempotently() -> None:
    records = parse_food_reference_archive(
        _archive(), FoodReferenceDataset.FOUNDATION
    )

    assert len(records) == 2
    assert records[0].external_id == "1001"
    assert records[0].food_category == "Vegetables"
    assert records[0].calories_per_100 == 41
    assert records[0].carbs_per_100 == Decimal("8.2")
    assert records[0].portions == (
        {"gram_weight": "61", "amount": "1", "description": "medium"},
    )

    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as session, session.begin():
        first = import_food_references(
            session, FoodReferenceDataset.FOUNDATION, records
        )
        second = import_food_references(
            session, FoodReferenceDataset.FOUNDATION, records
        )

    assert (first.created, first.updated, first.unchanged, first.complete) == (
        2,
        0,
        0,
        1,
    )
    assert (second.created, second.updated, second.unchanged) == (0, 0, 2)
    with Session(engine) as session:
        assert (
            session.scalar(select(func.count()).select_from(FoodReferenceItem)) == 2
        )


def _archive() -> bytes:
    files = {
        "foundation_food.csv": [{"fdc_id": "1001"}, {"fdc_id": "1002"}],
        "food.csv": [
            {
                "fdc_id": "1001",
                "data_type": "Foundation",
                "description": "Carrots, raw",
                "food_category_id": "11",
                "publication_date": "2026-04-30",
            },
            {
                "fdc_id": "1002",
                "data_type": "Foundation",
                "description": "Mystery vegetable",
                "food_category_id": "11",
                "publication_date": "2026-04-30",
            },
        ],
        "food_category.csv": [{"id": "11", "description": "Vegetables"}],
        "measure_unit.csv": [{"id": "9999", "name": "each"}],
        "food_nutrient.csv": [
            {"fdc_id": "1001", "nutrient_id": "1008", "amount": "41"},
            {"fdc_id": "1001", "nutrient_id": "1003", "amount": "0.93"},
            {"fdc_id": "1001", "nutrient_id": "1004", "amount": "0.24"},
            {"fdc_id": "1001", "nutrient_id": "1005", "amount": "9.6"},
            {"fdc_id": "1001", "nutrient_id": "1079", "amount": "1.4"},
        ],
        "food_portion.csv": [
            {
                "fdc_id": "1001",
                "amount": "1",
                "measure_unit_id": "9999",
                "portion_description": "medium",
                "modifier": "",
                "gram_weight": "61",
            }
        ],
    }
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        for filename, rows in files.items():
            text = io.StringIO()
            writer = csv.DictWriter(text, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
            archive.writestr(filename, text.getvalue())
    return output.getvalue()
