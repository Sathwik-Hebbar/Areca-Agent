import sys
import os
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.main import app
from backend.db.session import SessionLocal
from backend.db.models.core.user import User, UserRole
from backend.db.models.env.soil_sensor_reading import SoilSensorReading
from backend.auth.jwt_handler import hash_password, create_access_token
from backend.hardware.sensor_reader import read_npk, SERIAL_LOCK

client = TestClient(app)


@pytest.fixture(scope="module")
def setup_soil_test_env():
    db = SessionLocal()
    try:
        # Cleanup past test users
        for name in ["test_soil_user_1", "test_soil_user_2"]:
            u = db.query(User).filter(User.username == name).first()
            if u:
                db.delete(u)
        db.commit()

        # Create two test farmers
        u1 = User(
            username="test_soil_user_1",
            phone="9888811111",
            password_hash=hash_password("pw1"),
            role=UserRole.FARMER,
        )
        u2 = User(
            username="test_soil_user_2",
            phone="9888822222",
            password_hash=hash_password("pw2"),
            role=UserRole.FARMER,
        )
        db.add_all([u1, u2])
        db.commit()

        token1 = create_access_token({"sub": str(u1.id)})
        token2 = create_access_token({"sub": str(u2.id)})

        h1 = {"Authorization": f"Bearer {token1}"}
        h2 = {"Authorization": f"Bearer {token2}"}

        # Setup Farm & Crop Block for User 1
        client.post("/api/v1/core/profile", json={"full_name": "Soil Tester 1"}, headers=h1)
        res_f = client.post("/api/v1/core/farms", json={"farm_name": "Soil Test Farm 1"}, headers=h1)
        farm_id = res_f.json()["id"]

        res_b = client.post(
            "/api/v1/core/crop-blocks",
            json={
                "farm_id": farm_id,
                "block_name": "Soil Test Block 1",
                "planting_date": "2021-06-01",
            },
            headers=h1,
        )
        block_id_u1 = res_b.json()["id"]

        # Setup Profile for User 2
        client.post("/api/v1/core/profile", json={"full_name": "Soil Tester 2"}, headers=h2)

        yield {
            "h1": h1,
            "h2": h2,
            "block_id_u1": block_id_u1,
            "u1_id": str(u1.id),
            "u2_id": str(u2.id),
        }
    finally:
        # Teardown: explicitly delete env.soil_sensor_readings before deleting users,
        # so no test rows linger in the shared Neon DB after the suite.
        # Walk FK chain: User → FarmerProfile → Farm → CropBlock → SoilSensorReading
        from backend.db.models.core.farm import Farm
        from backend.db.models.core.crop_block import CropBlock
        from backend.db.models.core.farmer_profile import FarmerProfile

        for name in ["test_soil_user_1", "test_soil_user_2"]:
            u = db.query(User).filter(User.username == name).first()
            if u:
                fp = db.query(FarmerProfile).filter(FarmerProfile.user_id == u.id).first()
                if fp:
                    farm_ids = [f.id for f in db.query(Farm).filter(Farm.farmer_id == fp.id).all()]
                    if farm_ids:
                        block_ids = [
                            b.id for b in
                            db.query(CropBlock).filter(CropBlock.farm_id.in_(farm_ids)).all()
                        ]
                        if block_ids:
                            db.query(SoilSensorReading).filter(
                                SoilSensorReading.crop_block_id.in_(block_ids)
                            ).delete(synchronize_session=False)
                            db.flush()
                db.delete(u)
        db.commit()
        db.close()



def test_sensor_reader_pure_logic_and_formulas():
    """Verify single Modbus read_registers call, empirical P fit (4093 - raw), and validations."""
    with patch("minimalmodbus.Instrument") as mock_inst_cls:
        mock_inst = MagicMock()
        mock_inst_cls.return_value = mock_inst

        # 1. Normal valid telemetry: N=45, P_raw=4061 (derived=32.0), K=78
        mock_inst.read_registers.return_value = [45, 4061, 78]
        res = read_npk()
        assert res["status"] == "ok"
        assert res["nitrogen"] == 45.0
        assert res["phosphorus"] == 32.0  # 4093 - 4061
        assert res["potassium"] == 78.0
        assert res["raw_nitrogen"] == 45
        assert res["raw_phosphorus"] == 4061
        assert res["raw_potassium"] == 78
        assert res["unit"] == "uncalibrated prototype units"

        # Verify read_registers called once with 0x3002, 3 registers, functioncode=3
        mock_inst.read_registers.assert_called_with(0x3002, 3, functioncode=3)

        # 2. Open circuit / disconnected probe: raw 0 or 65535
        mock_inst.read_registers.return_value = [0, 4061, 78]
        res_zero = read_npk()
        assert res_zero["status"] == "invalid_reading"

        mock_inst.read_registers.return_value = [45, 65535, 78]
        res_max = read_npk()
        assert res_max["status"] == "invalid_reading"

        # 3. Out-of-bounds Phosphorus: raw_p > 4093 must be rejected to prevent DB check violation
        mock_inst.read_registers.return_value = [45, 4094, 78]
        res_p_oob = read_npk()
        assert res_p_oob["status"] == "invalid_reading"
        assert "4093" in res_p_oob["message"]

        # 4. Probe not inserted in soil (air baseline): raw_n=3, raw_p=4093, raw_k=0
        # All N, P, K must be reported as 0.0 only when all three conditions satisfy
        mock_inst.read_registers.return_value = [3, 4093, 0]
        res_baseline = read_npk()
        assert res_baseline["status"] == "no_soil_detected"
        assert res_baseline["nitrogen"] == 0.0
        assert res_baseline["phosphorus"] == 0.0
        assert res_baseline["potassium"] == 0.0
        assert res_baseline["raw_nitrogen"] == 3
        assert res_baseline["raw_phosphorus"] == 4093
        assert res_baseline["raw_potassium"] == 0
        assert "Insert the probe into soil" in res_baseline["message"]



def test_sensor_reader_serial_exception_maps_to_sensor_unavailable():
    """Verify serial/modbus exceptions map to sensor_unavailable, never raising 500."""
    with patch("minimalmodbus.Instrument") as mock_inst_cls:
        mock_inst = MagicMock()
        mock_inst_cls.return_value = mock_inst
        mock_inst.read_registers.side_effect = OSError("Port COM3 not found")

        res = read_npk()
        assert res["status"] == "sensor_unavailable"
        assert "COM3" in res["message"]
        assert res["unit"] == "uncalibrated prototype units"


def test_sensor_reader_busy_lock():
    """Verify non-blocking lock returns 'busy' status when serial port is already in use."""
    # Acquire lock in current thread
    acquired = SERIAL_LOCK.acquire(blocking=False)
    assert acquired is True
    try:
        res = read_npk()
        assert res["status"] == "busy"
        assert "currently in use" in res["message"]
    finally:
        SERIAL_LOCK.release()


def test_sensor_reader_port_released_after_each_call():
    """
    Verify that close_port_after_each_call=True is set on the Instrument so the
    COM port is fully released after every read. This is essential so QModMaster
    and USB converter replugging work without restarting the backend.
    """
    with patch("minimalmodbus.Instrument") as mock_inst_cls:
        mock_inst = MagicMock()
        mock_inst_cls.return_value = mock_inst
        # Normal successful read
        mock_inst.read_registers.return_value = [45, 4061, 78]

        res = read_npk()
        assert res["status"] == "ok"

        # Assert close_port_after_each_call was set to True
        assert mock_inst.close_port_after_each_call is True, (
            "close_port_after_each_call must be True so the COM port is released "
            "after every Modbus transaction, allowing QModMaster and replugging to work."
        )

        # Assert SERIAL_LOCK is free after the call (port was released inside lock)
        lock_free = SERIAL_LOCK.acquire(blocking=False)
        assert lock_free is True, "SERIAL_LOCK was not released after read_npk() returned."
        SERIAL_LOCK.release()


def test_endpoint_manual_read_always_stores(setup_soil_test_env):
    """Verify manual=True always persists reading to DB."""
    env = setup_soil_test_env
    block_id = env["block_id_u1"]
    h1 = env["h1"]

    with patch("backend.hardware.router.read_npk") as mock_read:
        mock_read.return_value = {
            "status": "ok",
            "nitrogen": 50.0,
            "phosphorus": 25.0,
            "potassium": 80.0,
            "raw_nitrogen": 50,
            "raw_phosphorus": 4068,
            "raw_potassium": 80,
            "unit": "uncalibrated prototype units",
            "calibration_status": "uncalibrated",
        }

        # First manual read
        resp1 = client.post(
            "/api/v1/hardware/soil/read",
            json={"crop_block_id": block_id, "manual": True},
            headers=h1,
        )
        assert resp1.status_code == 200
        data1 = resp1.json()
        assert data1["status"] == "ok"
        assert data1["stored"] is True
        assert data1["live_reading"]["nitrogen"] == 50.0
        assert data1["last_stored_reading"]["nitrogen"] == 50.0

        # Second manual read immediately after: should still store because manual=True
        resp2 = client.post(
            "/api/v1/hardware/soil/read",
            json={"crop_block_id": block_id, "manual": True},
            headers=h1,
        )
        assert resp2.status_code == 200
        data2 = resp2.json()
        assert data2["stored"] is True


def test_endpoint_auto_read_10_minute_storage_policy(setup_soil_test_env):
    """Verify manual=False does not store if last reading is < 10 minutes old."""
    env = setup_soil_test_env
    block_id = env["block_id_u1"]
    h1 = env["h1"]

    db = SessionLocal()
    # Count existing readings
    initial_count = db.query(SoilSensorReading).filter(SoilSensorReading.crop_block_id == block_id).count()
    db.close()

    with patch("backend.hardware.router.read_npk") as mock_read:
        mock_read.return_value = {
            "status": "ok",
            "nitrogen": 52.0,
            "phosphorus": 28.0,
            "potassium": 85.0,
            "raw_nitrogen": 52,
            "raw_phosphorus": 4065,
            "raw_potassium": 85,
            "unit": "uncalibrated prototype units",
            "calibration_status": "uncalibrated",
        }

        # Auto read (manual=False): within 10 minutes of previous manual test reads
        resp = client.post(
            "/api/v1/hardware/soil/read",
            json={"crop_block_id": block_id, "manual": False},
            headers=h1,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["stored"] is False  # Throttled by 10-minute policy
        assert data["live_reading"]["nitrogen"] == 52.0
        assert data["last_stored_reading"] is not None

        # Verify DB row count did not increase
        db = SessionLocal()
        final_count = db.query(SoilSensorReading).filter(SoilSensorReading.crop_block_id == block_id).count()
        db.close()
        assert final_count == initial_count


def test_endpoint_sensor_unavailable_never_stores(setup_soil_test_env):
    """Verify that when sensor is unavailable, nothing is stored in DB and last reading is returned."""
    env = setup_soil_test_env
    block_id = env["block_id_u1"]
    h1 = env["h1"]

    db = SessionLocal()
    count_before = db.query(SoilSensorReading).filter(SoilSensorReading.crop_block_id == block_id).count()
    db.close()

    with patch("backend.hardware.router.read_npk") as mock_read:
        mock_read.return_value = {
            "status": "sensor_unavailable",
            "message": "Serial port COM3 is in use by QModMaster",
            "unit": "uncalibrated prototype units",
            "calibration_status": "uncalibrated",
        }

        resp = client.post(
            "/api/v1/hardware/soil/read",
            json={"crop_block_id": block_id, "manual": True},
            headers=h1,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "sensor_unavailable"
        assert data["stored"] is False
        assert data["live_reading"] is None
        assert data["last_stored_reading"] is not None  # Fallback reading present

        db = SessionLocal()
        count_after = db.query(SoilSensorReading).filter(SoilSensorReading.crop_block_id == block_id).count()
        db.close()
        assert count_after == count_before


def test_endpoint_invalid_reading_never_stores(setup_soil_test_env):
    """Verify that invalid probe readings (0 / 65535 / p > 4093) are never stored."""
    env = setup_soil_test_env
    block_id = env["block_id_u1"]
    h1 = env["h1"]

    db = SessionLocal()
    count_before = db.query(SoilSensorReading).filter(SoilSensorReading.crop_block_id == block_id).count()
    db.close()

    with patch("backend.hardware.router.read_npk") as mock_read:
        mock_read.return_value = {
            "status": "invalid_reading",
            "message": "Probe or wiring fault detected",
            "unit": "uncalibrated prototype units",
            "calibration_status": "uncalibrated",
        }

        resp = client.post(
            "/api/v1/hardware/soil/read",
            json={"crop_block_id": block_id, "manual": True},
            headers=h1,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "invalid_reading"
        assert data["stored"] is False

        db = SessionLocal()
        count_after = db.query(SoilSensorReading).filter(SoilSensorReading.crop_block_id == block_id).count()
        db.close()
        assert count_after == count_before


def test_endpoint_no_soil_detected_never_stores(setup_soil_test_env):
    """The exact idle-air tuple is returned but never persisted, even manually."""
    env = setup_soil_test_env
    block_id = env["block_id_u1"]
    h1 = env["h1"]

    db = SessionLocal()
    count_before = (
        db.query(SoilSensorReading)
        .filter(SoilSensorReading.crop_block_id == block_id)
        .count()
    )
    db.close()

    with patch("backend.hardware.router.read_npk") as mock_read:
        mock_read.return_value = {
            "status": "no_soil_detected",
            "nitrogen": 0.0,
            "phosphorus": 0.0,
            "potassium": 0.0,
            "raw_nitrogen": 3,
            "raw_phosphorus": 4093,
            "raw_potassium": 0,
            "message": "No soil detected. Insert the probe into soil.",
            "unit": "uncalibrated prototype units",
            "calibration_status": "uncalibrated",
        }

        response = client.post(
            "/api/v1/hardware/soil/read",
            json={"crop_block_id": block_id, "manual": True},
            headers=h1,
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "no_soil_detected"
    assert payload["stored"] is False
    assert payload["live_reading"]["raw_nitrogen"] == 3
    assert payload["live_reading"]["raw_phosphorus"] == 4093
    assert payload["live_reading"]["raw_potassium"] == 0

    db = SessionLocal()
    count_after = (
        db.query(SoilSensorReading)
        .filter(SoilSensorReading.crop_block_id == block_id)
        .count()
    )
    db.close()
    assert count_after == count_before


def test_endpoint_forbidden_crop_block_ownership(setup_soil_test_env):
    """Verify 403 when farmer 2 attempts to read or query farmer 1's crop block."""
    env = setup_soil_test_env
    block_id_u1 = env["block_id_u1"]
    h2 = env["h2"]

    # User 2 attempting to read User 1's block
    resp_read = client.post(
        "/api/v1/hardware/soil/read",
        json={"crop_block_id": block_id_u1, "manual": True},
        headers=h2,
    )
    assert resp_read.status_code in (403, 404)

    # User 2 attempting to get latest for User 1's block
    resp_latest = client.get(
        f"/api/v1/hardware/soil/latest?crop_block_id={block_id_u1}",
        headers=h2,
    )
    assert resp_latest.status_code in (403, 404)


def test_get_latest_reading_endpoint(setup_soil_test_env):
    """Verify GET /api/v1/hardware/soil/latest returns the most recent reading."""
    env = setup_soil_test_env
    block_id = env["block_id_u1"]
    h1 = env["h1"]

    resp = client.get(
        f"/api/v1/hardware/soil/latest?crop_block_id={block_id}",
        headers=h1,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data is not None
    assert "nitrogen" in data
    assert "phosphorus" in data
    assert "potassium" in data
    assert data["unit"] == "uncalibrated prototype units"
