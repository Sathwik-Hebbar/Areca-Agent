from pydantic import BaseModel
from datetime import datetime


class DiseaseDetectionCreate(BaseModel):
    crop_block_id: str
    image_path: str
    predicted_disease: str
    cnn_confidence: float
    posterior_probability: float | None = None
    validated: bool = False


class DiseaseDetectionResponse(BaseModel):
    id: str
    crop_block_id: str
    image_path: str
    predicted_disease: str
    cnn_confidence: float
    posterior_probability: float | None = None
    validated: bool
    detected_at: datetime

    class Config:
        from_attributes = True
