from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.db.session import get_db
from backend.schemas.market import MarketPriceResponse
from backend.db.models.market.market_price import MarketPrice

router = APIRouter(prefix="/agents/market", tags=["Market Agent"])


@router.get("/prices", response_model=list[MarketPriceResponse])
def get_market_prices(mandi: str | None = Query(None), db: Session = Depends(get_db)):
    """
    Market Agent: Returns live and LSTM forecasted Mandi prices.
    """
    query = db.query(MarketPrice)
    if mandi:
        query = query.filter(MarketPrice.mandi_name == mandi)
    return query.order_by(MarketPrice.price_date.desc()).limit(20).all()
