import asyncio
import uuid
import logging
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.auth.jwt_handler import get_current_user
from backend.db.models.core.user import User
from backend.db.models.env.soil_sensor_reading import SoilSensorReading
from backend.core.router import _verify_crop_block_ownership
from backend.hardware.sensor_reader import read_npk
from backend.schemas.soil_sensor import (
    SoilReadRequest,
    SoilReadResponse,
    LiveSoilReading,
    SoilSensorReadingResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/hardware", tags=["Hardware Sensor"])


@router.post("/soil/read", response_model=SoilReadResponse)
async def read_soil_sensor(
    payload: SoilReadRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Reads soil NPK sensor via USB-to-RS485 Modbus RTU interface.
    - Runs blocking serial communication via asyncio.to_thread to prevent event-loop stalls.
    - All NPK values are in UNCALIBRATED prototype units.
    - Persists reading only if manual=True or if the last stored reading is older than 10 minutes.
    - Failed or invalid reads are never stored in the database.
    """
    # 1. Verify that the authenticated farmer owns this crop block
    _verify_crop_block_ownership(db, str(payload.crop_block_id), str(current_user.id))

    # 2. Query last stored reading for fallback display
    last_record = (
        db.query(SoilSensorReading)
        .filter(SoilSensorReading.crop_block_id == str(payload.crop_block_id))
        .order_by(SoilSensorReading.recorded_at.desc())
        .first()
    )
    last_stored_reading = (
        SoilSensorReadingResponse.model_validate(last_record) if last_record else None
    )

    # 3. Execute non-blocking threadpool serial read
    read_result = await asyncio.to_thread(read_npk)
    read_status = read_result.get("status", "sensor_unavailable")
    now_utc = datetime.now(timezone.utc)

    # 4. Never persist unavailable, busy, invalid, or air-baseline readings.
    if read_status != "ok":
        no_soil_live_reading = None
        if read_status == "no_soil_detected":
            no_soil_live_reading = LiveSoilReading(
                nitrogen=read_result.get("nitrogen"),
                phosphorus=read_result.get("phosphorus"),
                potassium=read_result.get("potassium"),
                raw_nitrogen=read_result.get("raw_nitrogen"),
                raw_phosphorus=read_result.get("raw_phosphorus"),
                raw_potassium=read_result.get("raw_potassium"),
                unit=read_result.get("unit", "uncalibrated prototype units"),
                calibration_status=read_result.get("calibration_status", "uncalibrated"),
            )
        return SoilReadResponse(
            status=read_status,
            live_reading=no_soil_live_reading,
            recorded_at=now_utc if no_soil_live_reading else None,
            stored=False,
            last_stored_reading=last_stored_reading,
            message=read_result.get("message", "Unable to acquire soil sensor reading."),
            unit="uncalibrated prototype units",
            calibration_status="uncalibrated",
        )

    # 5. Build live reading payload (UNCALIBRATED prototype units)
    live = LiveSoilReading(
        nitrogen=read_result["nitrogen"],
        phosphorus=read_result["phosphorus"],
        potassium=read_result["potassium"],
        raw_nitrogen=read_result["raw_nitrogen"],
        raw_phosphorus=read_result["raw_phosphorus"],
        raw_potassium=read_result["raw_potassium"],
        unit="uncalibrated prototype units",
        calibration_status="uncalibrated",
    )

    # 6. Evaluate 10-minute storage policy
    should_store = False
    if payload.manual:
        should_store = True
    elif last_record is None:
        should_store = True
    else:
        last_time = last_record.recorded_at
        if last_time.tzinfo is None:
            last_time = last_time.replace(tzinfo=timezone.utc)
        if (now_utc - last_time) >= timedelta(minutes=10):
            should_store = True

    if should_store:
        new_record = SoilSensorReading(
            crop_block_id=str(payload.crop_block_id),
            nitrogen=read_result["nitrogen"],
            phosphorus=read_result["phosphorus"],
            potassium=read_result["potassium"],
            raw_nitrogen=read_result["raw_nitrogen"],
            raw_phosphorus=read_result["raw_phosphorus"],
            raw_potassium=read_result["raw_potassium"],
            recorded_at=now_utc,
        )
        db.add(new_record)
        db.commit()
        db.refresh(new_record)
        last_stored_reading = SoilSensorReadingResponse.model_validate(new_record)
        stored_flag = True
    else:
        stored_flag = False

    return SoilReadResponse(
        status="ok",
        live_reading=live,
        recorded_at=now_utc,
        stored=stored_flag,
        last_stored_reading=last_stored_reading,
        message=read_result.get(
            "message",
            "Soil NPK reading acquired successfully (uncalibrated prototype units).",
        ),
        unit="uncalibrated prototype units",
        calibration_status="uncalibrated",
    )


@router.get("/soil/latest", response_model=SoilSensorReadingResponse | None)
def get_latest_soil_reading(
    crop_block_id: uuid.UUID = Query(..., description="Crop block ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieves the most recent persisted soil sensor reading for the given crop block.
    """
    _verify_crop_block_ownership(db, str(crop_block_id), str(current_user.id))

    latest_record = (
        db.query(SoilSensorReading)
        .filter(SoilSensorReading.crop_block_id == str(crop_block_id))
        .order_by(SoilSensorReading.recorded_at.desc())
        .first()
    )
    if not latest_record:
        return None

    return SoilSensorReadingResponse.model_validate(latest_record)
