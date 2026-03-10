"""Strategy parameters and runtime manager."""

from pydantic import BaseModel


class StrategyParams(BaseModel):
    """Configurable take-profit and stop-loss parameters."""

    take_profit_multipliers: list[float]
    stop_loss: float


class StrategyManager:
    """Thread-safe runtime manager for strategy parameters.

    Allows hot-updating TP/SL values via the API without restart.
    """

    def __init__(self, params: StrategyParams) -> None:
        self._params = params

    @property
    def params(self) -> StrategyParams:
        """Return current strategy parameters."""
        return self._params

    def update(
        self,
        take_profit_multipliers: list[float] | None = None,
        stop_loss: float | None = None,
    ) -> StrategyParams:
        """Update strategy parameters at runtime.

        Args:
            take_profit_multipliers: New TP multipliers list, or None to keep current.
            stop_loss: New stop-loss threshold, or None to keep current.

        Returns:
            Updated strategy parameters.
        """
        if take_profit_multipliers is not None:
            self._params.take_profit_multipliers = take_profit_multipliers
        if stop_loss is not None:
            self._params.stop_loss = stop_loss
        return self._params
