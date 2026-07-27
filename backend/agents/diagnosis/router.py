from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.db.session import get_db
from backend.db.models.agronomy.disease_detection import DiseaseDetection

router = APIRouter(prefix="/agents/diagnosis", tags=["Diagnosis Agent"])


@router.post("/validate/{detection_id}")
def validate_diagnosis(detection_id: str, db: Session = Depends(get_db)):
    """
    Diagnosis Agent: Runs Bayesian update combining CNN confidence with weather & activity context.
    """
    detection = db.query(DiseaseDetection).filter(DiseaseDetection.id == detection_id).first()
    if not detection:
        raise HTTPException(status_code=404, detail="Detection record not found")

    # Bayesian update logic stub
    prior = detection.cnn_confidence
    weather_factor = 1.15  # high humidity bonus
    posterior = min(0.99, prior * weather_factor)
    
    detection.posterior_probability = posterior
    detection.validated = posterior > 0.75
    db.commit()
    db.refresh(detection)

    return {
        "detection_id": detection.id,
        "predicted_disease": detection.predicted_disease,
        "cnn_confidence": detection.cnn_confidence,
        "posterior_probability": posterior,
        "validated": detection.validated
    }
