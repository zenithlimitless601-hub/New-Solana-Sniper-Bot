from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class Trade(SQLModel, table=True):
    __tablename__ = "trades"
    id: Optional[int] = Field(default=None, primary_key=True)
    token_id: int = Field(foreign_key="tokens.id", index=True)
    mode: str = Field(default="simulation", index=True)
    status: str = Field(default="open", index=True)
    entry_price: float
    entry_amount_usd: float
    entry_time: datetime = Field(default_factory=datetime.utcnow, index=True)
    exit_price: Optional[float] = None
    exit_time: Optional[datetime] = None
    roi: Optional[float] = None
    pnl_usd: Optional[float] = None
