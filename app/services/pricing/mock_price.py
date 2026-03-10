"""Mock price provider with random-walk simulation for paper trading."""

import asyncio
import random
from collections import defaultdict
from time import time

from app.services.pricing.base import PriceProvider

_MIN_PRICE = 1e-6
_DRIFT_MIN = -0.08
_DRIFT_MAX = 0.12
_UPDATE_INTERVAL_S = 1.0


class MockPriceProvider(PriceProvider):
    """Generates random-walk prices for simulation mode.

    Each token gets an initial random price in [0.001, 0.02] and drifts
    by -8% to +12% per update (at most once per second).
    """

    def __init__(self) -> None:
        self._prices: dict[str, float] = defaultdict(self._init_price)
        self._last_ts: dict[str, float] = {}

    @staticmethod
    def _init_price() -> float:
        return round(random.uniform(0.001, 0.02), 6)

    async def get_price(self, token_address: str) -> float:
        """Return the simulated price, applying drift if enough time has passed."""
        await asyncio.sleep(0)
        now = time()
        last = self._last_ts.get(token_address, 0.0)
        if now - last > _UPDATE_INTERVAL_S:
            p = self._prices[token_address]
            drift = random.uniform(_DRIFT_MIN, _DRIFT_MAX)
            p = max(_MIN_PRICE, p * (1 + drift))
            self._prices[token_address] = round(p, 8)
            self._last_ts[token_address] = now
        return self._prices[token_address]
