from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.db.session import engine, db_url
from backend.db.base import Base

# Import all models to ensure schema registration before table creation
import backend.db.models  # noqa

# Import routers
from backend.auth import auth_router
from backend.core import core_router
from backend.agents import (
    vision_router,
    diagnosis_router,
    weather_router,
    market_router,
    advisory_router,
    coordinator_router,
    learning_router,
    notifying_router
)

app = FastAPI(
    title="ArecaAgent Backend API",
    description="FastAPI monorepo for ArecaAgent multi-agent system (PostgreSQL 5-schema architecture)",
    version="0.2.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_db_check():
    """Ensure database tables are created (especially when running sqlite or local dev)."""
    if db_url.startswith("sqlite"):
        Base.metadata.create_all(bind=engine)


@app.get("/", tags=["Health Check"])
def root():
    return {
        "status": "healthy",
        "app": "ArecaAgent Monorepo Backend API",
        "version": "0.2.0",
        "environment": settings.ENVIRONMENT
    }


# Mount Routers under /api/v1
api_prefix = "/api/v1"
app.include_router(auth_router, prefix=api_prefix)
app.include_router(core_router, prefix=api_prefix)
app.include_router(vision_router, prefix=api_prefix)
app.include_router(diagnosis_router, prefix=api_prefix)
app.include_router(weather_router, prefix=api_prefix)
app.include_router(market_router, prefix=api_prefix)
app.include_router(advisory_router, prefix=api_prefix)
app.include_router(coordinator_router, prefix=api_prefix)
app.include_router(learning_router, prefix=api_prefix)
app.include_router(notifying_router, prefix=api_prefix)
