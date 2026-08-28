import asyncio
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session
from backend.db.session import get_db
from backend.db.models.core.user import User
from backend.db.models.agronomy.disease_detection import DiseaseDetection
from backend.auth.jwt_handler import get_current_user
from backend.schemas.disease import DiseaseDetectionResponse
from backend.core.router import _verify_crop_block_ownership
from backend.agents.vision.inference import run_vision_inference

router = APIRouter(prefix="/agents/vision", tags=["Vision Agent"])

UPLOADS_DIR = Path("E:/Areca-Agent/backend/data/uploads")


@router.post("/detect", response_model=DiseaseDetectionResponse, status_code=status.HTTP_201_CREATED)
async def detect_disease(
    crop_block_id: uuid.UUID = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Vision Agent Endpoint: Accepts leaf/fruit photo upload + crop_block_id.
    1. Verifies authenticated user owns the specified crop_block_id (raises 403 if not).
    2. Runs CNN disease inference (with 70% thresholding) in a worker thread pool.
    3. Saves uploaded image asset to local backend/data/uploads/.
    4. Inserts disease_detections record into agronomy schema.
    """
    # 1. Ownership check (reuses existing core/router.py helper)
    _verify_crop_block_ownership(db, str(crop_block_id), str(current_user.id))

    # 2. Read image bytes and run Vision inference in thread pool
    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    inference_result = await asyncio.to_thread(run_vision_inference, image_bytes)

    # 3. Save uploaded image to disk
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4()}_{file.filename}"
    saved_path = UPLOADS_DIR / filename
    with open(saved_path, "wb") as f:
        f.write(image_bytes)

    rel_image_path = f"uploads/{filename}"

    # 4. Save detection record to database
    detection = DiseaseDetection(
        crop_block_id=str(crop_block_id),
        image_path=rel_image_path,
        predicted_disease=inference_result["predicted_disease"],
        cnn_confidence=inference_result["confidence"],
        posterior_probability=None,
        validated=False,
    )
    db.add(detection)
    db.commit()
    db.refresh(detection)

    return detection
