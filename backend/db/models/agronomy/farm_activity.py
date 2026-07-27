import uuid
from datetime import date, datetime
from sqlalchemy import String, Float, Date, DateTime, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.db.base import Base
import enum


class ActivityType(str, enum.Enum):
    PLANTING = "planting"
    FERTILIZER = "fertilizer"
    SPRAYING = "spraying"
    IRRIGATION = "irrigation"
    PRUNING = "pruning"
    WEEDING = "weeding"
    HARVESTING = "harvesting"
    SOIL_TEST = "soil_test"
    OTHER = "other"


class LoggedVia(str, enum.Enum):
    APP = "app"
    SMS = "sms"
    AUTO = "auto"


class FarmActivity(Base):
    __tablename__ = "farm_activities"
    __table_args__ = {"schema": "agronomy"}

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    crop_block_id: Mapped[str] = mapped_column(String(36), ForeignKey("core.crop_blocks.id", ondelete="CASCADE"), nullable=False, index=True)
    activity_type: Mapped[ActivityType] = mapped_column(SQLEnum(ActivityType), nullable=False, index=True)
    activity_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    product_used: Mapped[str | None] = mapped_column(String(150), nullable=True, index=True)
    quantity: Mapped[float | None] = mapped_column(Float, nullable=True)
    quantity_unit: Mapped[str | None] = mapped_column(String(20), nullable=True)  # kg, litre, etc.
    cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    performed_by: Mapped[str | None] = mapped_column(String(100), nullable=True)  # self, labor
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # NPK ratio, target disease, etc.
    logged_via: Mapped[LoggedVia] = mapped_column(SQLEnum(LoggedVia), default=LoggedVia.APP)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    crop_block: Mapped["CropBlock"] = relationship("CropBlock", back_populates="activities")
