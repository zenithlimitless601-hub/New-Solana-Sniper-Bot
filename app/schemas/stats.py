from datetime import datetime
from pydantic import BaseModel


class StatsOut(BaseModel):
    total_roi: float
    win_rate: float
    avg_profit_usd: float
    max_drawdown: float


class EquityPoint(BaseModel):
    t: datetime
    equity: float


class EquityCurveOut(BaseModel):
    points: list[EquityPoint]
