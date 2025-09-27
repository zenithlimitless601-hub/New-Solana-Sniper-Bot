from pydantic import BaseModel


class StrategyConfigIn(BaseModel):
    take_profit_multipliers: list[float] | None = None
    stop_loss: float | None = None


class StrategyConfigOut(BaseModel):
    take_profit_multipliers: list[float]
    stop_loss: float
