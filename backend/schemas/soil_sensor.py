import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class SoilSensorReadingResponse(BaseModel):
    id: uuid.UUID
    crop_block_id: uuid.UUID
    nitrogen: float
    phosphorus: float
    potassium: float
    raw_nitrogen: int
    raw_phosphorus: int
    raw_potassium: int
    unit: str = "uncalibrated prototype units"
    calibration_status: str = "uncalibrated"
    recorded_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SoilReadRequest(BaseModel):
    crop_block_id: uuid.UUID
    manual: bool = False


class LiveSoilReading(BaseModel):
    nitrogen: float | None = None
    phosphorus: float | None = None
    potassium: float | None = None
    raw_nitrogen: int | None = None
    raw_phosphorus: int | None = None
    raw_potassium: int | None = None
    unit: str = "uncalibrated prototype units"
    calibration_status: str = "uncalibrated"


class SoilReadResponse(BaseModel):
    status: str  # "ok" | "sensor_unavailable" | "busy" | "invalid_reading" | "no_soil_detected"
    live_reading: LiveSoilReading | None = None
    recorded_at: datetime | None = None
    stored: bool = False
    last_stored_reading: SoilSensorReadingResponse | None = None
    message: str = ""
    unit: str = "uncalibrated prototype units"
    calibration_status: str = "uncalibrated"
