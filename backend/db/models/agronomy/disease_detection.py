import uuid
from datetime import datetime
from sqlalchemy import String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.db.base import Base


class DiseaseDetection(Base):
    __tablename__ = "disease_detections"
    __table_args__ = {"schema": "agronomy"}

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    crop_block_id: Mapped[str] = mapped_column(String(36), ForeignKey("core.crop_blocks.id", ondelete="CASCADE"), nullable=False, index=True)
    image_path: Mapped[str] = mapped_column(String(255), nullable=False)
    predicted_disease: Mapped[str] = mapped_column(String(100), nullable=False)
    cnn_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    posterior_probability: Mapped[float | None] = mapped_column(Float, nullable=True)  # Diagnosis Bayesian output
    validated: Mapped[bool] = mapped_column(Boolean, default=False)
    detected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    crop_block: Mapped["CropBlock"] = relationship("CropBlock", back_populates="disease_detections")
