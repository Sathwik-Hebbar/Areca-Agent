import io
import sys
import os
import pytest
from PIL import Image
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.main import app
from backend.config import settings
from backend.db.session import SessionLocal
from backend.db.models.core.user import User, UserRole
from backend.db.models.core.farmer_profile import FarmerProfile
from backend.db.models.core.farm import Farm
from backend.db.models.core.crop_block import CropBlock
from backend.auth.jwt_handler import hash_password, create_access_token
from backend.agents.vision.preprocess import preprocess_image_bytes, preprocess_image_keras
from backend.agents.vision.inference import run_vision_inference, run_pytorch_vision_inference
from backend.agents.vision.keras_inference import run_keras_vision_inference, KERAS_CLASS_MAPPING

client = TestClient(app)


def create_sample_image_bytes() -> bytes:
    """Helper to generate a valid RGB JPEG image in bytes."""
    img = Image.new("RGB", (300, 300), color=(100, 150, 200))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


@pytest.fixture(scope="module")
def setup_vision_env():
    db = SessionLocal()
    try:
        # Cleanup
        for name in ["test_vision_user_a", "test_vision_user_b"]:
            u = db.query(User).filter(User.username == name).first()
            if u:
                db.delete(u)
        db.commit()

        # Users A & B
        u_a = User(username="test_vision_user_a", phone="9333333331", password_hash=hash_password("p1"), role=UserRole.FARMER)
        u_b = User(username="test_vision_user_b", phone="9333333332", password_hash=hash_password("p2"), role=UserRole.FARMER)
        db.add_all([u_a, u_b])
        db.commit()

        token_a = create_access_token({"sub": str(u_a.id)})
        token_b = create_access_token({"sub": str(u_b.id)})

        h_a = {"Authorization": f"Bearer {token_a}"}
        h_b = {"Authorization": f"Bearer {token_b}"}

        # Create Profile & Farm & Crop Block for User A
        prof_a = FarmerProfile(user_id=u_a.id, full_name="Vision Tester A")
        db.add(prof_a)
        db.commit()

        farm_a = Farm(farmer_id=prof_a.id, farm_name="Vision Farm A")
        db.add(farm_a)
        db.commit()

        block_a = CropBlock(farm_id=farm_a.id, block_name="Vision Block A", planting_date="2020-01-01")
        db.add(block_a)
        db.commit()

        # Create Profile for User B
        prof_b = FarmerProfile(user_id=u_b.id, full_name="Vision Tester B")
        db.add(prof_b)
        db.commit()

        yield {
            "h_a": h_a,
            "h_b": h_b,
            "block_a_id": str(block_a.id),
        }
    finally:
        for name in ["test_vision_user_a", "test_vision_user_b"]:
            u = db.query(User).filter(User.username == name).first()
            if u:
                db.delete(u)
        db.commit()
        db.close()


def test_preprocessing_and_inference():
    img_bytes = create_sample_image_bytes()

    # 1. PyTorch Preprocessing output tensor shape
    tensor = preprocess_image_bytes(img_bytes)
    assert tensor.shape == (1, 3, 224, 224), f"Unexpected PyTorch tensor shape: {tensor.shape}"

    # 2. Keras Preprocessing output numpy array shape and scaling [-1, 1]
    keras_arr = preprocess_image_keras(img_bytes)
    assert keras_arr.shape == (1, 224, 224, 3), f"Unexpected Keras array shape: {keras_arr.shape}"
    assert keras_arr.min() >= -1.0 and keras_arr.max() <= 1.0, "Keras image preprocessing must scale to [-1, 1]"

    # 3. Keras Inference Direct
    keras_result = run_keras_vision_inference(img_bytes)
    assert "predicted_disease" in keras_result
    assert "confidence" in keras_result
    assert "inconclusive" in keras_result
    assert keras_result["predicted_disease"] in list(KERAS_CLASS_MAPPING.values()) + ["Inconclusive"]

    # 4. PyTorch Inference Direct
    pytorch_result = run_pytorch_vision_inference(img_bytes)
    assert "predicted_disease" in pytorch_result
    assert "confidence" in pytorch_result
    assert "inconclusive" in pytorch_result

    # 5. Unified Dispatcher with settings.VISION_BACKEND
    orig_backend = settings.VISION_BACKEND
    try:
        settings.VISION_BACKEND = "keras"
        res_k = run_vision_inference(img_bytes)
        assert res_k["backend"] in ["keras", "keras_stub"]

        settings.VISION_BACKEND = "pytorch"
        res_p = run_vision_inference(img_bytes)
        assert res_p["backend"] in ["pytorch", "pytorch_stub"]
    finally:
        settings.VISION_BACKEND = orig_backend


def test_vision_detect_endpoint(setup_vision_env):
    h_a = setup_vision_env["h_a"]
    h_b = setup_vision_env["h_b"]
    block_a_id = setup_vision_env["block_a_id"]

    img_bytes = create_sample_image_bytes()

    # 1. User A posts disease detection request
    res = client.post(
        "/api/v1/agents/vision/detect",
        data={"crop_block_id": block_a_id},
        files={"file": ("test_leaf.jpg", img_bytes, "image/jpeg")},
        headers=h_a,
    )
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["crop_block_id"] == block_a_id
    assert "predicted_disease" in data
    assert data["cnn_confidence"] > 0.0

    # 2. Cross-farmer access rejection (User B trying to run detection on User A's crop block)
    res_b = client.post(
        "/api/v1/agents/vision/detect",
        data={"crop_block_id": block_a_id},
        files={"file": ("test_leaf.jpg", img_bytes, "image/jpeg")},
        headers=h_b,
    )
    assert res_b.status_code == 403, "User B should be forbidden from uploading images to User A's crop block"


if __name__ == "__main__":
    pytest.main(["-v", __file__])
