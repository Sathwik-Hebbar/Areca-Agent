import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.db.session import engine
from backend.db.base import Base

logger = logging.getLogger(__name__)

# Import all models to ensure schema registration before table creation
import backend.db.models  # noqa

# Explicit direct router imports (decoupled from package __init__.py files)
from backend.auth.router import router as auth_router
from backend.core.router import router as core_router
from backend.agents.vision.router import router as vision_router
from backend.agents.diagnosis.router import router as diagnosis_router
from backend.agents.weather.router import router as weather_router
from backend.agents.market.router import router as market_router
from backend.agents.advisory.router import router as advisory_router
from backend.agents.coordinator.router import router as coordinator_router
from backend.agents.learning.router import router as learning_router
from backend.agents.notifying.router import router as notifying_router
from backend.hardware.router import router as hardware_router

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


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global crash guard: Ensures unhandled agent errors return 500 JSON without killing the uvicorn process."""
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal agent error: {str(exc)}", "path": str(request.url.path)},
    )


@app.on_event("startup")
def startup_checks():
    """Ensure database tables are created and warm up ML models asynchronously."""
    if settings.DATABASE_URL.startswith("sqlite"):
        Base.metadata.create_all(bind=engine)

    import threading

    def _bg_warmup():
        try:
            if getattr(settings, "VISION_BACKEND", "keras").lower() == "keras":
                from backend.agents.vision.keras_inference import warmup_keras_model
                warmup_keras_model()
        except Exception as e:
            logger.warning(f"Vision model warmup skipped: {e}")

    threading.Thread(target=_bg_warmup, daemon=True, name="model_warmup").start()


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
app.include_router(hardware_router, prefix=api_prefix)
