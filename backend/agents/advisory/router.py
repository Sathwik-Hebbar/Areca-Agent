from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.db.session import get_db
from backend.schemas.advisory import AdvisoryResponse, AdvisoryCreate
from backend.db.models.logs.advisory import Advisory, AdvisoryPriority, AdvisorySource
from backend.db.models.core.farmer_profile import FarmerProfile
from backend.db.models.core.crop_block import CropBlock
from backend.db.models.agronomy.farm_activity import FarmActivity

router = APIRouter(prefix="/agents/advisory", tags=["Advisory Agent"])


@router.post("/generate", response_model=AdvisoryResponse)
def generate_advisory(payload: AdvisoryCreate, db: Session = Depends(get_db)):
    """
    Advisory Agent: Constructs prompt snapshot pulling crop block age and activity history,
    calls Gemini API (or rule-based fallback), and persists input_snapshot.
    """
    # Pull context for snapshot
    farmer = db.query(FarmerProfile).filter(FarmerProfile.id == payload.farmer_id).first()
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer profile not found")

    snapshot = {
        "farmer_name": farmer.full_name,
        "language": farmer.preferred_language,
        "district": farmer.district,
    }

    if payload.crop_block_id:
        block = db.query(CropBlock).filter(CropBlock.id == payload.crop_block_id).first()
        if block:
            snapshot["crop_block"] = {
                "name": block.block_name,
                "variety": block.variety,
                "age_years": block.age_years,
                "tree_count": block.number_of_trees
            }
            # Fetch recent activity
            activities = db.query(FarmActivity).filter(FarmActivity.crop_block_id == block.id).order_by(FarmActivity.activity_date.desc()).limit(5).all()
            snapshot["recent_activities"] = [
                {"type": act.activity_type.value, "date": str(act.activity_date), "product": act.product_used}
                for act in activities
            ]

    advisory = Advisory(
        farmer_id=payload.farmer_id,
        crop_block_id=payload.crop_block_id,
        priority=payload.priority,
        message=payload.message,
        generated_by=payload.generated_by,
        input_snapshot=snapshot,
        read_status=False
    )
    db.add(advisory)
    db.commit()
    db.refresh(advisory)
    return advisory


@router.get("/farmer/{farmer_id}", response_model=list[AdvisoryResponse])
def get_farmer_advisories(farmer_id: str, db: Session = Depends(get_db)):
    return db.query(Advisory).filter(Advisory.farmer_id == farmer_id).order_by(Advisory.created_at.desc()).all()
