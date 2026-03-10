"""Abstract base class for price providers."""

from abc import ABC, abstractmethod


class PriceProvider(ABC):
    """Interface for fetching token prices."""

    @abstractmethod
    async def get_price(self, token_address: str) -> float:
        """Return the current price for the given token address."""
        ...
