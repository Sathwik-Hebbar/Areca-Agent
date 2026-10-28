import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve .env relative to this file's directory so the path is correct
# regardless of which working directory the FastAPI process is launched from.
_ENV_FILE = Path(__file__).parent / ".env"


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    SECRET_KEY: str = "development-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # --- Database ---
    # DATABASE_URL has NO default: if backend/.env is missing or the key is
    # empty, pydantic-settings will raise a ValidationError at startup with a
    # clear message rather than silently falling back to localhost.
    DATABASE_URL: str

    # Individual POSTGRES_* fields kept for local Docker-Compose dev only.
    # They are NOT used by session.py — DATABASE_URL is the single source of truth.
    POSTGRES_USER: str = "areca_user"
    POSTGRES_PASSWORD: str = "areca_pass"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "areca_agent_db"

    # --- External APIs ---
    GEMINI_API_KEY: str = ""
    GEMINI_DAILY_BUDGET_CAP: int = 100
    DATA_GOV_IN_API_KEY: str = ""

    # --- Vision Agent Backend ---
    VISION_BACKEND: str = "keras"  # "keras" | "pytorch"
    VISION_MODEL_STUB: bool = False

    # --- Soil Sensor Hardware (USB-to-RS485 Modbus RTU) ---
    SENSOR_COM_PORT: str = "COM8"
    SENSOR_BAUD_RATE: int = 4800
    SENSOR_SLAVE_ID: int = 1
    SENSOR_TIMEOUT_SECONDS: float = 1.0

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()

