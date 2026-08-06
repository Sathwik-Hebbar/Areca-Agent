import os
import torch
import torch.nn.functional as F
from pathlib import Path
from backend.config import settings
from backend.agents.vision.model import ArecanutCNN, CLASS_NAMES
from backend.agents.vision.preprocess import preprocess_image_bytes

WEIGHTS_PATH = Path(__file__).parent / "weights" / "arecanut_cnn.pt"
CONFIDENCE_THRESHOLD = 0.70  # 70% threshold per spec

_model_cache = None


def get_model() -> ArecanutCNN | None:
    """Lazy load and cache model weights if available."""
    global _model_cache
    if _model_cache is not None:
        return _model_cache

    if WEIGHTS_PATH.exists():
        try:
            model = ArecanutCNN(num_classes=len(CLASS_NAMES), pretrained=False)
            model.load_state_dict(torch.load(WEIGHTS_PATH, map_location="cpu"))
            model.eval()
            _model_cache = model
            return _model_cache
        except Exception as e:
            print(f"[WARN] Failed to load Vision model checkpoint: {e}")
            return None
    return None


def run_vision_inference(image_bytes: bytes) -> dict:
    """
    Run disease prediction on input image bytes.
    Enforces 70% confidence thresholding. If max score < 0.70, marks as inconclusive.
    Falls back to structured stub prediction if weights are missing or VISION_MODEL_STUB is true.
    """
    # 1. Always execute real image preprocessing to validate format/size (224x224 RGB)
    tensor = preprocess_image_bytes(image_bytes)

    # 2. Check if stub mode is active or weights are missing
    model = get_model()
    use_stub = getattr(settings, "VISION_MODEL_STUB", True) or (model is None)

    if use_stub:
        # Structured realistic stub inference
        predicted_disease = "yellow_leaf_disease"
        confidence = 0.91
        is_inconclusive = confidence < CONFIDENCE_THRESHOLD

        if is_inconclusive:
            return {
                "predicted_disease": "Inconclusive",
                "confidence": confidence,
                "inconclusive": True,
            }

        return {
            "predicted_disease": predicted_disease,
            "confidence": confidence,
            "inconclusive": False,
        }

    # 3. Real PyTorch model inference
    with torch.no_grad():
        outputs = model(tensor)
        probabilities = F.softmax(outputs, dim=1)[0]
        max_score, max_idx = torch.max(probabilities, dim=0)

        confidence = round(max_score.item(), 4)
        predicted_class = CLASS_NAMES[max_idx.item()]

        if confidence < CONFIDENCE_THRESHOLD:
            return {
                "predicted_disease": "Inconclusive",
                "confidence": confidence,
                "inconclusive": True,
            }

        return {
            "predicted_disease": predicted_class,
            "confidence": confidence,
            "inconclusive": False,
        }
