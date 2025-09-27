from pydantic import BaseModel


class StrategyParams(BaseModel):
    take_profit_multipliers: list[float]
    stop_loss: float


class StrategyManager:
    def __init__(self, params: StrategyParams) -> None:
        self._params = params

    @property
    def params(self) -> StrategyParams:
        return self._params

    def update(self, take_profit_multipliers: list[float] | None = None, stop_loss: float | None = None) -> StrategyParams:
        if take_profit_multipliers is not None:
            self._params.take_profit_multipliers = take_profit_multipliers
        if stop_loss is not None:
            self._params.stop_loss = stop_loss
        return self._params
