from sqlalchemy.orm import Session
from fastapi import HTTPException
from backend.db.models.core.farmer_profile import FarmerProfile
from backend.schemas.farmer import FarmerProfileCreate, FarmerProfileUpdate


def get_farmer_profile(db: Session, user_id: str) -> FarmerProfile:
    profile = db.query(FarmerProfile).filter(FarmerProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Farmer profile not found")
    return profile


def update_farmer_profile(db: Session, user_id: str, payload: FarmerProfileUpdate) -> FarmerProfile:
    profile = get_farmer_profile(db, user_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    db.commit()
    db.refresh(profile)
    return profile
