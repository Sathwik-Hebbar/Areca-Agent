from sqlalchemy.orm import Session
from fastapi import HTTPException
from backend.db.models.agronomy.farm_activity import FarmActivity, ActivityType
from backend.schemas.activity import ActivityCreate


def log_activity(db: Session, payload: ActivityCreate) -> FarmActivity:
    activity = FarmActivity(**payload.model_dump())
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity


def list_block_activities(db: Session, crop_block_id: str, activity_type: ActivityType | None = None) -> list[FarmActivity]:
    query = db.query(FarmActivity).filter(FarmActivity.crop_block_id == crop_block_id)
    if activity_type:
        query = query.filter(FarmActivity.activity_type == activity_type)
    return query.order_by(FarmActivity.activity_date.desc()).all()
