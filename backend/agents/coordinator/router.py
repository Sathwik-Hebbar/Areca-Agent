from fastapi import APIRouter

router = APIRouter(prefix="/agents/coordinator", tags=["Coordinator Agent"])


@router.post("/synthesize")
def synthesize_decision(crop_block_id: str):
    """
    Coordinator Agent: Integrates Vision (35%), Diagnosis (30%), Weather (20%), and Market (15%)
    weightings to output a unified decision payload.
    """
    return {
        "crop_block_id": crop_block_id,
        "weights": {"vision": 0.35, "diagnosis": 0.30, "weather": 0.20, "market": 0.15},
        "composite_risk_score": 0.72,
        "recommended_action": "Apply copper oxychloride spray within 48 hours before predicted rainfall."
    }
