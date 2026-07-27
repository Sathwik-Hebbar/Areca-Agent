from sqlalchemy.orm import Session
from fastapi import HTTPException
from backend.db.models.core.farm import Farm
from backend.schemas.farm import FarmCreate, FarmUpdate


def create_farm(db: Session, farmer_id: str, payload: FarmCreate) -> Farm:
    farm = Farm(farmer_id=farmer_id, **payload.model_dump())
    db.add(farm)
    db.commit()
    db.refresh(farm)
    return farm


def list_farms(db: Session, farmer_id: str) -> list[Farm]:
    return db.query(Farm).filter(Farm.farmer_id == farmer_id).all()


def get_farm(db: Session, farm_id: str, farmer_id: str) -> Farm:
    farm = db.query(Farm).filter(Farm.id == farm_id, Farm.farmer_id == farmer_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    return farm


def update_farm(db: Session, farm_id: str, farmer_id: str, payload: FarmUpdate) -> Farm:
    farm = get_farm(db, farm_id, farmer_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(farm, field, value)
    db.commit()
    db.refresh(farm)
    return farm
