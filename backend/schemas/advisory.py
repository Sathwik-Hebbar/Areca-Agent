from pydantic import BaseModel
from datetime import datetime
from backend.db.models.logs.advisory import AdvisoryPriority, AdvisorySource


class AdvisoryCreate(BaseModel):
    farmer_id: str
    crop_block_id: str | None = None
    priority: AdvisoryPriority = AdvisoryPriority.MEDIUM
    message: str
    generated_by: AdvisorySource = AdvisorySource.GEMINI
    input_snapshot: dict | None = None


class FeedbackCreate(BaseModel):
    advisory_id: str
    farmer_id: str
    rating: int  # 1-5
    outcome_notes: str | None = None


class AdvisoryResponse(BaseModel):
    id: str
    farmer_id: str
    crop_block_id: str | None = None
    priority: AdvisoryPriority
    message: str
    generated_by: AdvisorySource
    input_snapshot: dict | None = None
    read_status: bool
    created_at: datetime

    class Config:
        from_attributes = True
