"""Trade response schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class TradeOut(BaseModel):
    """Single trade record with entry/exit data and PnL."""

    id: int
    token_id: int
    mode: str
    status: str
    entry_price: float
    entry_amount_usd: float
    entry_time: datetime
    exit_price: float | None = None
    exit_time: datetime | None = None
    roi: float | None = None
    pnl_usd: float | None = None


class TradeListOut(BaseModel):
    """Paginated list of trades."""

    items: list[TradeOut]
    total: int = Field(...)
