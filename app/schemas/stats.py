"""Trading statistics and equity curve schemas."""

from datetime import datetime

from pydantic import BaseModel


class StatsOut(BaseModel):
    """Aggregate trading performance metrics."""

    total_roi: float
    win_rate: float
    avg_profit_usd: float
    max_drawdown: float


class EquityPoint(BaseModel):
    """Single point on the equity curve."""

    t: datetime
    equity: float


class EquityCurveOut(BaseModel):
    """Cumulative equity curve from closed trades."""

    points: list[EquityPoint]
