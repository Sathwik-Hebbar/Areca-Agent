from sqlalchemy.orm import Session
from fastapi import HTTPException
from backend.db.models.core.crop_block import CropBlock
from backend.schemas.crop_block import CropBlockCreate, CropBlockUpdate


def create_crop_block(db: Session, payload: CropBlockCreate) -> CropBlock:
    block = CropBlock(**payload.model_dump())
    db.add(block)
    db.commit()
    db.refresh(block)
    return block


def list_crop_blocks(db: Session, farm_id: str) -> list[CropBlock]:
    return db.query(CropBlock).filter(CropBlock.farm_id == farm_id).all()


def get_crop_block(db: Session, block_id: str) -> CropBlock:
    block = db.query(CropBlock).filter(CropBlock.id == block_id).first()
    if not block:
        raise HTTPException(status_code=404, detail="Crop block not found")
    return block


def update_crop_block(db: Session, block_id: str, payload: CropBlockUpdate) -> CropBlock:
    block = get_crop_block(db, block_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(block, field, value)
    db.commit()
    db.refresh(block)
    return block
