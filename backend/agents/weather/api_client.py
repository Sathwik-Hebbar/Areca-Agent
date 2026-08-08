import logging
import httpx
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from backend.db.models.env.weather_reading import WeatherReading, WeatherSource

logger = logging.getLogger(__name__)

# Default coordinates for Shivamogga/Dakshina Kannada region if unconfigured
DEFAULT_LAT = 12.9141
DEFAULT_LON = 74.8560


def get_grid_region_key(lat: float, lon: float) -> str:
    """
    Rounds latitude and longitude to 2 decimal places to create a ~1.1 km grid cell region_key.
    All farms within the same grid cell share a single weather cache.
    """
    return f"grid_{round(lat, 2):.2f}_{round(lon, 2):.2f}"


def fetch_live_weather(lat: float | None = None, lon: float | None = None) -> dict:
    """
    Fetches current weather conditions from Open-Meteo API (no API key required).
    URL: https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,rain

    If Open-Meteo is unreachable or network fails, returns explicit synthetic_fallback conditions.
    """
    use_default = (lat is None or lon is None)
    target_lat = DEFAULT_LAT if use_default else lat
    target_lon = DEFAULT_LON if use_default else lon

    location_source = "default_fallback" if use_default else "farm_coordinates"
    region_key = get_grid_region_key(target_lat, target_lon)

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": target_lat,
        "longitude": target_lon,
        "current": "temperature_2m,relative_humidity_2m,rain",
    }

    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(url, params=params)
            if resp.status_code == 200:
                data = resp.json()
                current_data = data.get("current", {})

                temp = float(current_data.get("temperature_2m", 26.5))
                hum = float(current_data.get("relative_humidity_2m", 82.0))
                rain = float(current_data.get("rain", 0.0))

                return {
                    "temperature": temp,
                    "humidity": hum,
                    "rainfall_mm": rain,
                    "region_key": region_key,
                    "location_source": location_source,
                    "lat": target_lat,
                    "lon": target_lon,
                    "weather_source": WeatherSource.API,
                    "is_synthetic": False,
                }
            else:
                logger.warning(f"Open-Meteo API returned status {resp.status_code}: {resp.text}")
    except Exception as e:
        logger.warning(f"Open-Meteo API connection error: {e}")

    # Explicit synthetic fallback when Open-Meteo API is unreachable
    logger.warning("Open-Meteo API unreachable. Using explicit synthetic_fallback data.")
    return {
        "temperature": 26.5,
        "humidity": 88.0,
        "rainfall_mm": 12.5,
        "region_key": region_key,
        "location_source": location_source,
        "lat": target_lat,
        "lon": target_lon,
        "weather_source": WeatherSource.SYNTHETIC_FALLBACK,
        "is_synthetic": True,
    }


def backfill_historical_weather(
    db: Session,
    farm_id: str | None,
    region_key: str,
    lat: float | None = None,
    lon: float | None = None,
    days: int = 14,
) -> int:
    """
    Backfills past 14 days of real historical weather from Open-Meteo Historical Archive API
    at 6-hour sample intervals (56 readings) with source=WeatherSource.HISTORICAL_BACKFILL.
    Ensures ARIMA time-series models have sufficient historical data (>= 14 readings) immediately on farm creation.
    """
    target_lat = DEFAULT_LAT if lat is None else lat
    target_lon = DEFAULT_LON if lon is None else lon

    end_date = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    start_date = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")

    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": target_lat,
        "longitude": target_lon,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": "temperature_2m,relative_humidity_2m,rain",
    }

    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(url, params=params)
            if resp.status_code != 200:
                logger.warning(f"Open-Meteo Historical Archive returned status {resp.status_code}")
                return 0

            data = resp.json()
            hourly = data.get("hourly", {})
            times = hourly.get("time", [])
            temps = hourly.get("temperature_2m", [])
            hums = hourly.get("relative_humidity_2m", [])
            rains = hourly.get("rain", [])

            readings_to_add = []
            # Sample every 6 hours (6-hourly intervals)
            for idx in range(0, len(times), 6):
                dt_str = times[idx]
                dt = datetime.fromisoformat(dt_str).replace(tzinfo=timezone.utc)
                temp = float(temps[idx]) if temps[idx] is not None else 25.0
                hum = float(hums[idx]) if hums[idx] is not None else 80.0
                rain = float(rains[idx]) if rains[idx] is not None else 0.0

                readings_to_add.append(
                    WeatherReading(
                        farm_id=farm_id,
                        region_key=region_key,
                        temperature=temp,
                        humidity=hum,
                        rainfall_mm=rain,
                        source=WeatherSource.HISTORICAL_BACKFILL,
                        recorded_at=dt,
                    )
                )

            if readings_to_add:
                db.add_all(readings_to_add)
                db.commit()
                logger.info(f"Backfilled {len(readings_to_add)} historical readings for region {region_key}")
                return len(readings_to_add)

    except Exception as e:
        logger.warning(f"Failed to backfill historical weather from Open-Meteo: {e}")

    return 0
