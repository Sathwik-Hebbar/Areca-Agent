import uuid
from datetime import datetime
from sqlalchemy import String, Float, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.db.base import Base
import enum


class IrrigationType(str, enum.Enum):
    DRIP = "drip"
    FLOOD = "flood"
    SPRINKLER = "sprinkler"
    RAINFED = "rainfed"


class Farm(Base):
    __tablename__ = "farms"
    __table_args__ = {"schema": "core"}

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    farmer_id: Mapped[str] = mapped_column(String(36), ForeignKey("core.farmer_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    farm_name: Mapped[str] = mapped_column(String(100), nullable=False)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_area_acres: Mapped[float | None] = mapped_column(Float, nullable=True)
    soil_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    irrigation_type: Mapped[IrrigationType | None] = mapped_column(SQLEnum(IrrigationType), default=IrrigationType.DRIP)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    farmer: Mapped["FarmerProfile"] = relationship("FarmerProfile", back_populates="farms")
    crop_blocks: Mapped[list["CropBlock"]] = relationship("CropBlock", back_populates="farm", cascade="all, delete-orphan")
    iot_devices: Mapped[list["IoTDevice"]] = relationship("IoTDevice", back_populates="farm", cascade="all, delete-orphan")
    weather_readings: Mapped[list["WeatherReading"]] = relationship("WeatherReading", back_populates="farm", cascade="all, delete-orphan")
