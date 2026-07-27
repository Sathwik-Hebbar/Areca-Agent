from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from backend.db.session import get_db
from backend.schemas.disease import DiseaseDetectionResponse, DiseaseDetectionCreate
from backend.db.models.agronomy.disease_detection import DiseaseDetection

router = APIRouter(prefix="/agents/vision", tags=["Vision Agent"])


@router.post("/detect", response_model=DiseaseDetectionResponse)
async def detect_disease(
    crop_block_id: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Vision Agent: Predicts disease from uploaded leaf/fruit image using CNN.
    """
    # Dummy mock predictions until trained CNN weights are loaded
    file_path = f"uploads/{file.filename}"
    mock_disease = "Koleroga (Mahali / Fruit Rot)"
    mock_confidence = 0.88

    detection = DiseaseDetection(
        crop_block_id=crop_block_id,
        image_path=file_path,
        predicted_disease=mock_disease,
        cnn_confidence=mock_confidence,
        validated=False
    )
    db.add(detection)
    db.commit()
    db.refresh(detection)
    return detection
