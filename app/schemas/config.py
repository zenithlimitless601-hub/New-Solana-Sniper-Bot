"""Strategy configuration schemas."""

from pydantic import BaseModel


class StrategyConfigIn(BaseModel):
    """Input schema for updating strategy parameters."""

    take_profit_multipliers: list[float] | None = None
    stop_loss: float | None = None


class StrategyConfigOut(BaseModel):
    """Output schema for current strategy parameters."""

    take_profit_multipliers: list[float]
    stop_loss: float
