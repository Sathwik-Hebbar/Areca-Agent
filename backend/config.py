import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    SECRET_KEY: str = "development-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    POSTGRES_USER: str = "areca_user"
    POSTGRES_PASSWORD: str = "areca_pass"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "areca_agent_db"
    DATABASE_URL: str = "postgresql://areca_user:areca_pass@localhost:5432/areca_agent_db"

    GEMINI_API_KEY: str = ""
    GEMINI_DAILY_BUDGET_CAP: int = 100

    WEATHER_API_KEY: str = ""
    DATA_GOV_IN_API_KEY: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
