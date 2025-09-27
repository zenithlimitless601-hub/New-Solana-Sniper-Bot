from abc import ABC, abstractmethod


class PriceProvider(ABC):
    @abstractmethod
    async def get_price(self, token_address: str) -> float: ...
