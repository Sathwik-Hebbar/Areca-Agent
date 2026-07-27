from pydantic import BaseModel
from datetime import date, datetime
from backend.db.models.agronomy.farm_activity import ActivityType, LoggedVia


class ActivityCreate(BaseModel):
    crop_block_id: str
    activity_type: ActivityType
    activity_date: date
    product_used: str | None = None
    quantity: float | None = None
    quantity_unit: str | None = None
    cost: float | None = None
    performed_by: str | None = None
    details: dict | None = None
    logged_via: LoggedVia = LoggedVia.APP


class ActivityResponse(BaseModel):
    id: str
    crop_block_id: str
    activity_type: ActivityType
    activity_date: date
    product_used: str | None = None
    quantity: float | None = None
    quantity_unit: str | None = None
    cost: float | None = None
    performed_by: str | None = None
    details: dict | None = None
    logged_via: LoggedVia
    created_at: datetime

    class Config:
        from_attributes = True
