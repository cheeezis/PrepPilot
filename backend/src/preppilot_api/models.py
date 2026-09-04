from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, Index, Numeric, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Food(Base):
    __tablename__ = "foods"
    __table_args__ = (
        CheckConstraint("length(trim(name)) > 0", name="ck_foods_name_not_blank"),
        CheckConstraint("base_unit IN ('g', 'ml')", name="ck_foods_base_unit"),
        CheckConstraint("calories_kcal >= 0", name="ck_foods_calories_nonnegative"),
        CheckConstraint("protein_g >= 0", name="ck_foods_protein_nonnegative"),
        CheckConstraint(
            "carbohydrates_g >= 0", name="ck_foods_carbohydrates_nonnegative"
        ),
        CheckConstraint("fat_g >= 0", name="ck_foods_fat_nonnegative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    base_unit: Mapped[str] = mapped_column(String(2))
    calories_kcal: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    protein_g: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    carbohydrates_g: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    fat_g: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


Index("uq_foods_name_ci", func.lower(Food.name), unique=True)
