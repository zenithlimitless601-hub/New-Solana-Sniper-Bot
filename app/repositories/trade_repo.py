from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Trade


class TradeRepo:
    async def create_open(self, session: AsyncSession, data: dict) -> Trade:
        trade = Trade(**data)
        session.add(trade)
        await session.flush()
        return trade

    async def close(self, session: AsyncSession, trade: Trade, exit_price: float) -> Trade:
        trade.exit_price = exit_price
        trade.exit_time = datetime.utcnow()
        trade.status = "closed"
        trade.roi = (exit_price - trade.entry_price) / trade.entry_price
        trade.pnl_usd = trade.entry_amount_usd * trade.roi
        await session.flush()
        return trade

    async def list_trades(self, session: AsyncSession, status: str | None = None, limit: int = 100, offset: int = 0) -> list[Trade]:
        stmt = select(Trade).order_by(Trade.id.desc()).limit(limit).offset(offset)
        if status:
            stmt = stmt.where(Trade.status == status)
        res = await session.execute(stmt)
        return list(res.scalars().all())

    async def get_open(self, session: AsyncSession) -> list[Trade]:
        res = await session.execute(select(Trade).where(Trade.status == "open").order_by(Trade.id.asc()))
        return list(res.scalars().all())

    async def get_by_id(self, session: AsyncSession, trade_id: int) -> Trade | None:
        return await session.get(Trade, trade_id)  # type: ignore
