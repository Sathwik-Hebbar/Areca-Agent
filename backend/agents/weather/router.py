from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.db.session import get_db
from backend.schemas.weather import WeatherReadingResponse
from backend.db.models.env.weather_reading import WeatherReading

router = APIRouter(prefix="/agents/weather", tags=["Weather Agent"])


@router.get("/current/{farm_id}", response_model=list[WeatherReadingResponse])
def get_current_weather(farm_id: str, db: Session = Depends(get_db)):
    """
    Weather Agent: Fetches latest weather readings and ARIMA forecasts for a farm.
    """
    readings = db.query(WeatherReading).filter(WeatherReading.farm_id == farm_id).order_by(WeatherReading.recorded_at.desc()).limit(10).all()
    return readings
