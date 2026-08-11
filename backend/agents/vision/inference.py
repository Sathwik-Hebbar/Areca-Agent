"""
Vision Agent Inference Dispatcher.

Supports dual backends:
- "keras": Uses Keras MobileNetV2 (mobilenetv2_best.h5) with [-1, 1] scaling
- "pytorch": Uses PyTorch MobileNetV2 (arecanut_cnn.pt) with ImageNet normalization

Configured via settings.VISION_BACKEND ("keras" | "pytorch").
"""

import os
import torch
import torch.nn.functional as F
from pathlib import Path
from backend.config import settings
from backend.agents.vision.model import ArecanutCNN, CLASS_NAMES
from backend.agents.vision.preprocess import preprocess_image_bytes

PYTORCH_WEIGHTS_PATH = Path(__file__).parent / "weights" / "arecanut_cnn.pt"
CONFIDENCE_THRESHOLD = 0.70  # 70% threshold per spec

_pytorch_model_cache = None


def get_pytorch_model() -> ArecanutCNN | None:
    """Lazy load and cache PyTorch model weights if available."""
    global _pytorch_model_cache
    if _pytorch_model_cache is not None:
        return _pytorch_model_cache

    if PYTORCH_WEIGHTS_PATH.exists():
        try:
            model = ArecanutCNN(num_classes=len(CLASS_NAMES), pretrained=False)
            model.load_state_dict(torch.load(PYTORCH_WEIGHTS_PATH, map_location="cpu"))
            model.eval()
            _pytorch_model_cache = model
            return _pytorch_model_cache
        except Exception as e:
            print(f"[WARN] Failed to load PyTorch Vision model checkpoint: {e}")
            return None
    return None


def run_pytorch_vision_inference(image_bytes: bytes) -> dict:
    """
    Run disease prediction on input image bytes using the PyTorch model.
    """
    # 1. Always execute real image preprocessing to validate format/size (224x224 RGB)
    tensor = preprocess_image_bytes(image_bytes)

    # 2. Check if stub mode is active or weights are missing
    model = get_pytorch_model()
    use_stub = getattr(settings, "VISION_MODEL_STUB", False) or (model is None)

    if use_stub:
        predicted_disease = "yellow_leaf_disease"
        confidence = 0.91
        is_inconclusive = confidence < CONFIDENCE_THRESHOLD

        return {
            "predicted_disease": "Inconclusive" if is_inconclusive else predicted_disease,
            "confidence": confidence,
            "inconclusive": is_inconclusive,
            "backend": "pytorch_stub",
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
                "backend": "pytorch",
            }

        return {
            "predicted_disease": predicted_class,
            "confidence": confidence,
            "inconclusive": False,
            "backend": "pytorch",
        }


def run_vision_inference(image_bytes: bytes) -> dict:
    """
    Unified entry point for Vision Agent inference.
    Dispatches to configured backend ('keras' or 'pytorch') via settings.VISION_BACKEND.
    """
    backend_choice = getattr(settings, "VISION_BACKEND", "keras").lower()

    if backend_choice == "keras":
        from backend.agents.vision.keras_inference import run_keras_vision_inference
        return run_keras_vision_inference(image_bytes)
    else:
        return run_pytorch_vision_inference(image_bytes)
