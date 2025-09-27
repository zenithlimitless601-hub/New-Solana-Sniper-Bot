from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.trade_repo import TradeRepo
from app.services.pricing.base import PriceProvider
from app.services.trading.base import Trader


class SimulatorTrader(Trader):
    def __init__(self, price_provider: PriceProvider, session_factory) -> None:
        self.price_provider = price_provider
        self.session_factory = session_factory
        self.trade_repo = TradeRepo()

    async def buy(self, session: AsyncSession, token_id: int, mode: str, entry_price: float, amount_usd: float):
        data = {
            "token_id": token_id,
            "mode": mode,
            "status": "open",
            "entry_price": entry_price,
            "entry_amount_usd": amount_usd,
        }
        return await self.trade_repo.create_open(session, data)

    async def sell(self, session: AsyncSession, trade, exit_price: float):
        return await self.trade_repo.close(session, trade, exit_price)
