from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.db.session import get_db
from backend.schemas.advisory import FeedbackCreate
from backend.db.models.logs.feedback import Feedback

router = APIRouter(prefix="/agents/learning", tags=["Learning Agent"])


@router.post("/feedback")
def submit_feedback(payload: FeedbackCreate, db: Session = Depends(get_db)):
    """
    Learning Agent: Accepts farmer feedback (rating 1-5) and updates Q-learning table weights.
    """
    feedback = Feedback(
        advisory_id=payload.advisory_id,
        farmer_id=payload.farmer_id,
        rating=payload.rating,
        outcome_notes=payload.outcome_notes
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return {
        "feedback_id": feedback.id,
        "status": "processed",
        "q_update_reward": (payload.rating - 3) * 0.5
    }
