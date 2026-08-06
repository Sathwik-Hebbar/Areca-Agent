import io
import torch
from PIL import Image
from torchvision import transforms

# ImageNet normalization statistics expected by MobileNetV2
NORM_MEAN = [0.485, 0.456, 0.406]
NORM_STD = [0.229, 0.224, 0.225]

# Standard evaluation/inference transform: resize 224x224, to tensor, normalize
eval_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=NORM_MEAN, std=NORM_STD),
])

# Standard training transform for normal volume classes
train_standard_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.RandomHorizontalFlip(p=0.5),
    transforms.RandomRotation(degrees=15),
    transforms.ColorJitter(brightness=0.1, contrast=0.1),
    transforms.ToTensor(),
    transforms.Normalize(mean=NORM_MEAN, std=NORM_STD),
])

# Heavy augmentation transform specifically for low-volume classes (healthy_foot, bud_borer, stem_bleeding)
train_heavy_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.RandomHorizontalFlip(p=0.5),
    transforms.RandomVerticalFlip(p=0.3),
    transforms.RandomRotation(degrees=30),
    transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.2),
    transforms.RandomAffine(degrees=0, scale=(0.8, 1.2), translate=(0.1, 0.1)),
    transforms.ToTensor(),
    transforms.Normalize(mean=NORM_MEAN, std=NORM_STD),
])


def preprocess_image_bytes(image_bytes: bytes) -> torch.Tensor:
    """
    Preprocess raw image bytes into a 4D batch tensor (1, 3, 224, 224) ready for CNN inference.
    """
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    tensor = eval_transform(image)
    return tensor.unsqueeze(0)  # Shape: (1, 3, 224, 224)


def get_train_transform(is_low_volume: bool = False):
    """
    Return training transform pipeline. Applies heavier augmentation for low-volume classes.
    """
    if is_low_volume:
        return train_heavy_transform
    return train_standard_transform
