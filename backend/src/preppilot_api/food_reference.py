import csv
import io
import zipfile
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from enum import StrEnum
from functools import lru_cache
from pathlib import PurePosixPath
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from sqlalchemy import select
from sqlalchemy.orm import Session

from preppilot_api.models import FoodReferenceItem
from preppilot_api.recipe_imports import normalize_text

FOODDATA_CENTRAL_SOURCE_NAME = "fooddata_central"
_NUTRIENT_IDS = {
    "calories": "1008",
    "protein": "1003",
    "fat": "1004",
    "total_carbs": "1005",
    "fiber": "1079",
}


class FoodReferenceError(RuntimeError):
    pass


class FoodReferencePayloadError(FoodReferenceError):
    pass


class FoodReferenceUnavailableError(FoodReferenceError):
    pass


class FoodReferenceDataset(StrEnum):
    FOUNDATION = "foundation"
    SR_LEGACY = "sr_legacy"

    @property
    def url(self) -> str:
        if self is FoodReferenceDataset.FOUNDATION:
            return (
                "https://fdc.nal.usda.gov/fdc-datasets/"
                "FoodData_Central_foundation_food_csv_2026-04-30.zip"
            )
        return (
            "https://fdc.nal.usda.gov/fdc-datasets/"
            "FoodData_Central_sr_legacy_food_csv_2018-04.zip"
        )

    @property
    def release(self) -> str:
        if self is FoodReferenceDataset.FOUNDATION:
            return "2026-04-30"
        return "2018-04"

    @property
    def membership_filename(self) -> str:
        if self is FoodReferenceDataset.FOUNDATION:
            return "foundation_food.csv"
        return "sr_legacy_food.csv"

    @property
    def data_type(self) -> str:
        if self is FoodReferenceDataset.FOUNDATION:
            return "Foundation"
        return "SR Legacy"


BinaryFetcher = Callable[[str, float], bytes]


@dataclass(frozen=True)
class FoodReferenceRecord:
    external_id: str
    data_type: str
    description: str
    food_category: str | None
    publication_date: str | None
    calories_per_100: Decimal | None
    protein_per_100: Decimal | None
    total_carbs_per_100: Decimal | None
    fiber_per_100: Decimal | None
    carbs_per_100: Decimal | None
    fat_per_100: Decimal | None
    portions: tuple[dict[str, object], ...]


@dataclass(frozen=True)
class FoodReferenceImportResult:
    dataset: FoodReferenceDataset
    parsed: int
    created: int
    updated: int
    unchanged: int
    complete: int


@dataclass(frozen=True)
class FoodReferenceSource:
    timeout_seconds: float = 60.0
    fetch_bytes: BinaryFetcher | None = None

    def download(self, dataset: FoodReferenceDataset) -> bytes:
        fetcher = self.fetch_bytes or fetch_binary
        return fetcher(dataset.url, self.timeout_seconds)


def parse_food_reference_archive(
    payload: bytes, dataset: FoodReferenceDataset
) -> tuple[FoodReferenceRecord, ...]:
    try:
        archive = zipfile.ZipFile(io.BytesIO(payload))
    except (zipfile.BadZipFile, OSError) as error:
        raise FoodReferencePayloadError("invalid FoodData Central ZIP archive") from error

    with archive:
        member_ids = {
            row["fdc_id"]
            for row in _rows(archive, dataset.membership_filename)
            if row.get("fdc_id")
        }
        if not member_ids:
            raise FoodReferencePayloadError(
                "FoodData Central archive contains no dataset members"
            )
        foods = {
            row["fdc_id"]: row
            for row in _rows(archive, "food.csv")
            if row.get("fdc_id") in member_ids and row.get("description")
        }
        if not foods:
            raise FoodReferencePayloadError(
                "FoodData Central archive contains no foods"
            )
        categories = {
            row["id"]: row.get("description", "").strip()
            for row in _optional_rows(archive, "food_category.csv")
            if row.get("id")
        }
        measures = {
            row["id"]: row.get("name", "").strip()
            for row in _optional_rows(archive, "measure_unit.csv")
            if row.get("id")
        }
        nutrients: dict[str, dict[str, Decimal]] = {
            external_id: {} for external_id in foods
        }
        nutrient_names = {value: key for key, value in _NUTRIENT_IDS.items()}
        for row in _rows(archive, "food_nutrient.csv"):
            values = nutrients.get(row.get("fdc_id", ""))
            nutrient_name = nutrient_names.get(row.get("nutrient_id", ""))
            amount = _decimal(row.get("amount"))
            if values is not None and nutrient_name is not None and amount is not None:
                values[nutrient_name] = amount.quantize(
                    Decimal("0.0001"), rounding=ROUND_HALF_UP
                )

        portions: dict[str, list[dict[str, object]]] = {
            external_id: [] for external_id in foods
        }
        for row in _optional_rows(archive, "food_portion.csv"):
            target = portions.get(row.get("fdc_id", ""))
            gram_weight = _decimal(row.get("gram_weight"))
            amount = _decimal(row.get("amount"))
            if target is None or gram_weight is None or gram_weight <= 0:
                continue
            portion: dict[str, object] = {"gram_weight": str(gram_weight)}
            if amount is not None:
                portion["amount"] = str(amount)
            measure = measures.get(row.get("measure_unit_id", ""), "")
            description = (
                row.get("portion_description", "").strip()
                or row.get("modifier", "").strip()
                or measure
            )
            if description:
                portion["description"] = description
            target.append(portion)

    records: list[FoodReferenceRecord] = []
    for external_id, food in foods.items():
        values = nutrients[external_id]
        total_carbs = values.get("total_carbs")
        fiber = values.get("fiber")
        available_carbs = (
            total_carbs - fiber
            if total_carbs is not None
            and fiber is not None
            and total_carbs >= fiber
            else None
        )
        category = categories.get(food.get("food_category_id", ""))
        records.append(
            FoodReferenceRecord(
                external_id=external_id,
                data_type=dataset.data_type,
                description=food["description"].strip(),
                food_category=category or None,
                publication_date=food.get("publication_date", "").strip() or None,
                calories_per_100=values.get("calories"),
                protein_per_100=values.get("protein"),
                total_carbs_per_100=total_carbs,
                fiber_per_100=fiber,
                carbs_per_100=available_carbs,
                fat_per_100=values.get("fat"),
                portions=tuple(portions[external_id]),
            )
        )
    return tuple(records)


def import_food_references(
    session: Session,
    dataset: FoodReferenceDataset,
    records: Iterable[FoodReferenceRecord],
) -> FoodReferenceImportResult:
    parsed_records = tuple(records)
    existing = {
        item.external_id: item
        for item in session.scalars(
            select(FoodReferenceItem).where(
                FoodReferenceItem.source_name == FOODDATA_CENTRAL_SOURCE_NAME
            )
        )
    }
    now = datetime.now(UTC)
    created = 0
    updated = 0
    unchanged = 0
    complete = 0
    for record in parsed_records:
        values = _record_values(record, dataset)
        if all(
            value is not None
            for value in (
                record.calories_per_100,
                record.protein_per_100,
                record.carbs_per_100,
                record.fat_per_100,
            )
        ):
            complete += 1
        item = existing.get(record.external_id)
        if item is None:
            session.add(
                FoodReferenceItem(
                    source_name=FOODDATA_CENTRAL_SOURCE_NAME,
                    external_id=record.external_id,
                    imported_at=now,
                    **values,
                )
            )
            created += 1
            continue
        if all(getattr(item, key) == value for key, value in values.items()):
            unchanged += 1
            continue
        for key, value in values.items():
            setattr(item, key, value)
        item.imported_at = now
        updated += 1
    session.flush()
    return FoodReferenceImportResult(
        dataset=dataset,
        parsed=len(parsed_records),
        created=created,
        updated=updated,
        unchanged=unchanged,
        complete=complete,
    )


def fetch_binary(url: str, timeout: float) -> bytes:
    request = Request(url, headers={"User-Agent": "PrepPilot/0.1"})
    try:
        with urlopen(request, timeout=timeout) as response:
            return bytes(response.read())
    except (HTTPError, URLError, TimeoutError, OSError) as error:
        raise FoodReferenceUnavailableError(
            "FoodData Central reference download failed"
        ) from error


@lru_cache
def get_food_reference_source() -> FoodReferenceSource:
    return FoodReferenceSource()


def _record_values(
    record: FoodReferenceRecord, dataset: FoodReferenceDataset
) -> dict[str, object]:
    return {
        "data_type": record.data_type,
        "description": record.description,
        "normalized_description": normalize_text(record.description),
        "food_category": record.food_category,
        "publication_date": record.publication_date,
        "dataset_release": dataset.release,
        "calories_per_100": record.calories_per_100,
        "protein_per_100": record.protein_per_100,
        "total_carbs_per_100": record.total_carbs_per_100,
        "fiber_per_100": record.fiber_per_100,
        "carbs_per_100": record.carbs_per_100,
        "fat_per_100": record.fat_per_100,
        "portions": list(record.portions),
    }


def _rows(archive: zipfile.ZipFile, filename: str) -> Iterable[dict[str, str]]:
    member = _member(archive, filename)
    if member is None:
        raise FoodReferencePayloadError(f"archive is missing {filename}")
    with archive.open(member) as raw:
        with io.TextIOWrapper(raw, encoding="utf-8-sig", errors="replace") as text:
            yield from csv.DictReader(text)


def _optional_rows(
    archive: zipfile.ZipFile, filename: str
) -> Iterable[dict[str, str]]:
    member = _member(archive, filename)
    if member is None:
        return
    with archive.open(member) as raw:
        with io.TextIOWrapper(raw, encoding="utf-8-sig", errors="replace") as text:
            yield from csv.DictReader(text)


def _member(archive: zipfile.ZipFile, filename: str) -> str | None:
    return next(
        (
            member
            for member in archive.namelist()
            if PurePosixPath(member).name.casefold() == filename.casefold()
        ),
        None,
    )


def _decimal(value: str | None) -> Decimal | None:
    if value is None or not value.strip():
        return None
    try:
        number = Decimal(value)
    except InvalidOperation:
        return None
    return number if number.is_finite() and number >= 0 else None
