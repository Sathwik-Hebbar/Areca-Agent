import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.db.base import Base


class FarmerProfile(Base):
    __tablename__ = "farmer_profiles"
    __table_args__ = {"schema": "core"}

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("core.users.id", ondelete="CASCADE"), nullable=False, unique=True)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    village: Mapped[str | None] = mapped_column(String(100), nullable=True)
    taluk: Mapped[str | None] = mapped_column(String(100), nullable=True)
    district: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    pincode: Mapped[str | None] = mapped_column(String(10), nullable=True)
    preferred_language: Mapped[str] = mapped_column(String(20), default="en")
    preferred_mandi: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship("User", back_populates="farmer_profile")
    farms: Mapped[list["Farm"]] = relationship("Farm", back_populates="farmer", cascade="all, delete-orphan")
    advisories: Mapped[list["Advisory"]] = relationship("Advisory", back_populates="farmer", cascade="all, delete-orphan")
