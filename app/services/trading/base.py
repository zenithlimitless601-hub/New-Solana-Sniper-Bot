from abc import ABC, abstractmethod
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.trade import Trade


class Trader(ABC):
    @abstractmethod
    async def buy(self, session: AsyncSession, token_id: int, mode: str, entry_price: float, amount_usd: float) -> Trade: ...

    @abstractmethod
    async def sell(self, session: AsyncSession, trade: Trade, exit_price: float) -> Trade: ...
