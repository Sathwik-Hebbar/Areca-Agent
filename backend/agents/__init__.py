from backend.agents.vision import vision_router
from backend.agents.diagnosis import diagnosis_router
from backend.agents.weather import weather_router
from backend.agents.market import market_router
from backend.agents.advisory import advisory_router
from backend.agents.coordinator import coordinator_router
from backend.agents.learning import learning_router
from backend.agents.notifying import notifying_router

__all__ = [
    "vision_router",
    "diagnosis_router",
    "weather_router",
    "market_router",
    "advisory_router",
    "coordinator_router",
    "learning_router",
    "notifying_router"
]
