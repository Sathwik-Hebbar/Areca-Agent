from pydantic import BaseModel
from datetime import datetime


class FarmerProfileCreate(BaseModel):
    full_name: str
    village: str | None = None
    taluk: str | None = None
    district: str | None = None
    state: str | None = None
    pincode: str | None = None
    preferred_language: str = "en"
    preferred_mandi: str | None = None


class FarmerProfileUpdate(BaseModel):
    full_name: str | None = None
    village: str | None = None
    taluk: str | None = None
    district: str | None = None
    state: str | None = None
    pincode: str | None = None
    preferred_language: str | None = None
    preferred_mandi: str | None = None


class FarmerProfileResponse(BaseModel):
    id: str
    user_id: str
    full_name: str
    village: str | None = None
    taluk: str | None = None
    district: str | None = None
    state: str | None = None
    pincode: str | None = None
    preferred_language: str
    preferred_mandi: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True
