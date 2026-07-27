import uuid
from datetime import date, datetime
from sqlalchemy import String, Integer, Float, Date, DateTime, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.db.base import Base
import enum


class BlockStatus(str, enum.Enum):
    ACTIVE = "active"
    REMOVED = "removed"
    REPLANTED = "replanted"


class CropBlock(Base):
    __tablename__ = "crop_blocks"
    __table_args__ = {"schema": "core"}

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    farm_id: Mapped[str] = mapped_column(String(36), ForeignKey("core.farms.id", ondelete="CASCADE"), nullable=False, index=True)
    block_name: Mapped[str] = mapped_column(String(100), nullable=False)
    variety: Mapped[str | None] = mapped_column(String(100), nullable=True)  # Mangala, Sumangala, South Kanara, etc.
    planting_date: Mapped[date] = mapped_column(Date, nullable=False)
    number_of_trees: Mapped[int] = mapped_column(Integer, default=0)
    spacing_meters: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[BlockStatus] = mapped_column(SQLEnum(BlockStatus), default=BlockStatus.ACTIVE)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    farm: Mapped["Farm"] = relationship("Farm", back_populates="crop_blocks")
    activities: Mapped[list["FarmActivity"]] = relationship("FarmActivity", back_populates="crop_block", cascade="all, delete-orphan")
    disease_detections: Mapped[list["DiseaseDetection"]] = relationship("DiseaseDetection", back_populates="crop_block", cascade="all, delete-orphan")

    @property
    def age_years(self) -> float:
        """Derived property: calculate crop block age in years dynamically."""
        if not self.planting_date:
            return 0.0
        delta = date.today() - self.planting_date
        return round(delta.days / 365.25, 2)
