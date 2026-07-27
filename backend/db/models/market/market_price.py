import uuid
from datetime import date
from sqlalchemy import String, Float, Date
from sqlalchemy.orm import Mapped, mapped_column
from backend.db.base import Base


class MarketPrice(Base):
    __tablename__ = "market_prices"
    __table_args__ = {"schema": "market"}

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    mandi_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    commodity: Mapped[str] = mapped_column(String(100), default="arecanut", index=True)
    price_per_kg: Mapped[float] = mapped_column(Float, nullable=False)
    price_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(100), default="data.gov.in")
