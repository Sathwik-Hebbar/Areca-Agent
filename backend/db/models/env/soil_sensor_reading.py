from datetime import datetime
from sqlalchemy import text, Numeric, Integer, ForeignKey, DateTime, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.db.base import Base


class SoilSensorReading(Base):
    """
    Soil NPK sensor reading collected via direct Modbus RTU RS485 serial connection.
    
    IMPORTANT NOTE ON CALIBRATION:
    NPK values are reported in uncalibrated prototype units.
    Phosphorus is computed via an empirical unverified fit (4093 - raw).
    All values must be treated as uncalibrated prototype units in comments, API responses, and UI.
    """
    __tablename__ = "soil_sensor_readings"
    __table_args__ = (
        CheckConstraint("phosphorus >= 0", name="chk_soil_phosphorus_non_negative"),
        Index("ix_env_soil_sensor_readings_crop_block_recorded", "crop_block_id", text("recorded_at DESC")),
        {"schema": "env"},
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    crop_block_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("core.crop_blocks.id", ondelete="CASCADE"),
        nullable=False,
    )

    # N/P/K in uncalibrated prototype units
    nitrogen: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False, comment="Uncalibrated prototype units")
    phosphorus: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False, comment="Uncalibrated prototype units: empirical fit 4093 - raw")
    potassium: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False, comment="Uncalibrated prototype units")

    # Raw Modbus holding register telemetry (FC03: 0x3002, 0x3003, 0x3004)
    raw_nitrogen: Mapped[int] = mapped_column(Integer, nullable=False)
    raw_phosphorus: Mapped[int] = mapped_column(Integer, nullable=False)
    raw_potassium: Mapped[int] = mapped_column(Integer, nullable=False)

    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    crop_block: Mapped["CropBlock"] = relationship("CropBlock", back_populates="soil_readings")
