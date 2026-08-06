import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class DiseaseDetectionCreate(BaseModel):
    crop_block_id: uuid.UUID
    image_path: str
    predicted_disease: str
    cnn_confidence: float
    posterior_probability: float | None = None
    validated: bool = False


class DiseaseDetectionResponse(BaseModel):
    id: uuid.UUID
    crop_block_id: uuid.UUID
    image_path: str
    predicted_disease: str
    cnn_confidence: float
    posterior_probability: float | None = None
    validated: bool
    detected_at: datetime

    model_config = ConfigDict(from_attributes=True)
