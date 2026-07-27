from pydantic import BaseModel
from datetime import datetime
from backend.db.models.core.farm import IrrigationType


class FarmCreate(BaseModel):
    farm_name: str
    latitude: float | None = None
    longitude: float | None = None
    total_area_acres: float | None = None
    soil_type: str | None = None
    irrigation_type: IrrigationType = IrrigationType.DRIP


class FarmUpdate(BaseModel):
    farm_name: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    total_area_acres: float | None = None
    soil_type: str | None = None
    irrigation_type: IrrigationType | None = None


class FarmResponse(BaseModel):
    id: str
    farmer_id: str
    farm_name: str
    latitude: float | None = None
    longitude: float | None = None
    total_area_acres: float | None = None
    soil_type: str | None = None
    irrigation_type: IrrigationType | None = None
    created_at: datetime

    class Config:
        from_attributes = True
