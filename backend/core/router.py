from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.db.session import get_db
from backend.db.models.core.user import User
from backend.auth.jwt_handler import get_current_user
from backend.schemas.farmer import FarmerProfileUpdate, FarmerProfileResponse
from backend.schemas.farm import FarmCreate, FarmUpdate, FarmResponse
from backend.schemas.crop_block import CropBlockCreate, CropBlockUpdate, CropBlockResponse
from backend.schemas.activity import ActivityCreate, ActivityResponse
from backend.db.models.agronomy.farm_activity import ActivityType
from backend.core.farmer_service import get_farmer_profile, update_farmer_profile
from backend.core.farm_service import create_farm, list_farms, get_farm, update_farm
from backend.core.crop_block_service import create_crop_block, list_crop_blocks, get_crop_block, update_crop_block
from backend.core.activity_service import log_activity, list_block_activities

router = APIRouter(prefix="/core", tags=["Core Farmer & Land Management"])


# Farmer Profile Endpoints
@router.get("/profile", response_model=FarmerProfileResponse)
def read_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_farmer_profile(db, current_user.id)


@router.put("/profile", response_model=FarmerProfileResponse)
def edit_profile(payload: FarmerProfileUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return update_farmer_profile(db, current_user.id, payload)


# Farm Endpoints
@router.post("/farms", response_model=FarmResponse)
def add_farm(payload: FarmCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = get_farmer_profile(db, current_user.id)
    return create_farm(db, profile.id, payload)


@router.get("/farms", response_model=list[FarmResponse])
def get_user_farms(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = get_farmer_profile(db, current_user.id)
    return list_farms(db, profile.id)


@router.get("/farms/{farm_id}", response_model=FarmResponse)
def get_single_farm(farm_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = get_farmer_profile(db, current_user.id)
    return get_farm(db, farm_id, profile.id)


@router.put("/farms/{farm_id}", response_model=FarmResponse)
def edit_farm(farm_id: str, payload: FarmUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = get_farmer_profile(db, current_user.id)
    return update_farm(db, farm_id, profile.id, payload)


# Crop Block Endpoints
@router.post("/crop-blocks", response_model=CropBlockResponse)
def add_crop_block(payload: CropBlockCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return create_crop_block(db, payload)


@router.get("/farms/{farm_id}/crop-blocks", response_model=list[CropBlockResponse])
def get_farm_crop_blocks(farm_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return list_crop_blocks(db, farm_id)


@router.get("/crop-blocks/{block_id}", response_model=CropBlockResponse)
def get_single_crop_block(block_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_crop_block(db, block_id)


@router.put("/crop-blocks/{block_id}", response_model=CropBlockResponse)
def edit_crop_block(block_id: str, payload: CropBlockUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return update_crop_block(db, block_id, payload)


# Farm Activity Endpoints
@router.post("/activities", response_model=ActivityResponse)
def record_activity(payload: ActivityCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return log_activity(db, payload)


@router.get("/crop-blocks/{block_id}/activities", response_model=list[ActivityResponse])
def get_activities_by_block(block_id: str, activity_type: ActivityType | None = Query(None), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return list_block_activities(db, block_id, activity_type)
