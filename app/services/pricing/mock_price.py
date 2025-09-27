import asyncio
import random
from collections import defaultdict
from time import time
from app.services.pricing.base import PriceProvider


class MockPriceProvider(PriceProvider):
    def __init__(self) -> None:
        self._prices: dict[str, float] = defaultdict(self._init_price)
        self._last_ts: dict[str, float] = {}

    def _init_price(self) -> float:
        return round(random.uniform(0.001, 0.02), 6)

    async def get_price(self, token_address: str) -> float:
        await asyncio.sleep(0)
        now = time()
        last = self._last_ts.get(token_address, 0.0)
        if now - last > 1:
            p = self._prices[token_address]
            drift = random.uniform(-0.08, 0.12)
            p = max(1e-6, p * (1 + drift))
            self._prices[token_address] = round(p, 8)
            self._last_ts[token_address] = now
        return self._prices[token_address]
