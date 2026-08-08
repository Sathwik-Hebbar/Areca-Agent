import uuid
import enum
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from backend.db.models.env.weather_reading import WeatherSource


class LocationSource(str, enum.Enum):
    FARM_COORDINATES = "farm_coordinates"
    DEFAULT_FALLBACK = "default_fallback"


class DiseaseRiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class DiseaseRiskFactorBreakdown(BaseModel):
    humidity_points: float
    temperature_points: float
    rainfall_points: float


class DiseaseRiskScore(BaseModel):
    score: float  # 0.0 to 100.0
    level: DiseaseRiskLevel
    confidence_level: str  # "verified_api" vs "unverified_synthetic"
    is_synthetic: bool = False
    factors: DiseaseRiskFactorBreakdown


class WeatherForecastItem(BaseModel):
    timestamp: datetime
    predicted_temperature: float
    predicted_humidity: float
    predicted_rainfall_mm: float
    forecast_model: str  # "arima" or "exponential_moving_average"


class WeatherReadingResponse(BaseModel):
    id: uuid.UUID
    farm_id: uuid.UUID | None = None
    region_key: str | None = None
    temperature: float
    humidity: float
    rainfall_mm: float
    source: WeatherSource
    recorded_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WeatherAgentResponse(BaseModel):
    id: uuid.UUID
    farm_id: uuid.UUID | None = None
    region_key: str
    location_source: LocationSource
    temperature: float
    humidity: float
    rainfall_mm: float
    source: WeatherSource
    recorded_at: datetime
    disease_risk: DiseaseRiskScore
    forecast: list[WeatherForecastItem] = []

    model_config = ConfigDict(from_attributes=True)
