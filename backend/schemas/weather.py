from pydantic import BaseModel
from datetime import datetime
from backend.db.models.env.weather_reading import WeatherSource


class WeatherReadingResponse(BaseModel):
    id: str
    farm_id: str
    temperature: float
    humidity: float
    rainfall_mm: float
    source: WeatherSource
    recorded_at: datetime

    class Config:
        from_attributes = True
