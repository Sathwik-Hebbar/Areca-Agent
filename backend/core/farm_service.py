from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from backend.db.models.core.farm import Farm
from backend.schemas.farm import FarmCreate, FarmUpdate


def create_farm(db: Session, farmer_id: str, data: FarmCreate) -> Farm:
    farm = Farm(farmer_id=str(farmer_id), **data.model_dump())
    db.add(farm)
    db.commit()
    db.refresh(farm)
    return farm


def get_farm(db: Session, farm_id: str) -> Farm:
    farm = db.query(Farm).filter(Farm.id == str(farm_id)).first()
    if not farm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farm not found",
        )
    return farm


def list_farms_for_farmer(db: Session, farmer_id: str) -> list[Farm]:
    return (
        db.query(Farm)
        .filter(Farm.farmer_id == str(farmer_id))
        .order_by(Farm.created_at.desc())
        .all()
    )


def update_farm(db: Session, farm_id: str, data: FarmUpdate) -> Farm:
    farm = get_farm(db, farm_id)
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(farm, field, value)
    db.commit()
    db.refresh(farm)
    return farm


def delete_farm(db: Session, farm_id: str) -> bool:
    """Hard delete farm -- cascades to crop_blocks, iot_devices, activities via DB FK ON DELETE rules."""
    farm = get_farm(db, farm_id)
    db.delete(farm)
    db.commit()
    return True
