from pydantic import BaseModel
from datetime import date


class MarketPriceResponse(BaseModel):
    id: str
    mandi_name: str
    commodity: str
    price_per_kg: float
    price_date: date
    source: str

    class Config:
        from_attributes = True
