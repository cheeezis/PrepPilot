from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Recipe(Base):
    __tablename__ = "recipes"
    __table_args__ = (
        CheckConstraint("length(trim(source_name)) > 0", name="ck_recipes_source"),
        CheckConstraint("length(trim(external_id)) > 0", name="ck_recipes_external_id"),
        CheckConstraint("length(trim(source_url)) > 0", name="ck_recipes_source_url"),
        CheckConstraint("length(trim(title)) > 0", name="ck_recipes_title"),
        CheckConstraint(
            "category in ('breakfast', 'lunch', 'dinner')",
            name="ck_recipes_category",
        ),
        CheckConstraint("servings > 0", name="ck_recipes_servings_positive"),
        CheckConstraint(
            "calories_per_serving > 0", name="ck_recipes_calories_positive"
        ),
        CheckConstraint(
            "protein_per_serving >= 0", name="ck_recipes_protein_nonnegative"
        ),
        CheckConstraint("carbs_per_serving >= 0", name="ck_recipes_carbs_nonnegative"),
        CheckConstraint("fat_per_serving >= 0", name="ck_recipes_fat_nonnegative"),
        CheckConstraint("length(content_hash) = 64", name="ck_recipes_content_hash"),
        UniqueConstraint(
            "source_name", "external_id", name="uq_recipes_source_external"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    source_name: Mapped[str] = mapped_column(String(100))
    external_id: Mapped[str] = mapped_column(String(300))
    source_url: Mapped[str] = mapped_column(Text)
    title: Mapped[str] = mapped_column(String(300))
    category: Mapped[str] = mapped_column(String(20))
    servings: Mapped[int] = mapped_column(Integer)
    calories_per_serving: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    protein_per_serving: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    carbs_per_serving: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    fat_per_serving: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    ingredients: Mapped[list[str]] = mapped_column(JSON)
    instructions: Mapped[list[str]] = mapped_column(JSON)
    preparation_minutes: Mapped[int | None] = mapped_column(Integer)
    cooking_minutes: Mapped[int | None] = mapped_column(Integer)
    raw_payload: Mapped[dict[str, object]] = mapped_column(JSON)
    content_hash: Mapped[str] = mapped_column(String(64))
    imported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    license_name: Mapped[str] = mapped_column(String(200))
    attribution_text: Mapped[str] = mapped_column(Text)
