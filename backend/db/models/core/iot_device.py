import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.db.base import Base


class IoTDevice(Base):
    __tablename__ = "iot_devices"
    __table_args__ = {"schema": "core"}

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    farm_id: Mapped[str] = mapped_column(String(36), ForeignKey("core.farms.id", ondelete="CASCADE"), nullable=False, index=True)
    device_token: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    device_type: Mapped[str] = mapped_column(String(50), default="soil_moisture_v1")
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    farm: Mapped["Farm"] = relationship("Farm", back_populates="iot_devices")
    soil_readings: Mapped[list["SoilSensorReading"]] = relationship("SoilSensorReading", back_populates="device", cascade="all, delete-orphan")
