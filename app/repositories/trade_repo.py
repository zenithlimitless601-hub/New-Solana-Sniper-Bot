"""Repository for Trade CRUD operations."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Trade


class TradeRepo:
    """Data-access layer for the trades table."""

    async def create_open(self, session: AsyncSession, data: dict) -> Trade:
        """Create a new trade with status 'open'."""
        trade = Trade(**data)
        session.add(trade)
        await session.flush()
        return trade

    async def close(self, session: AsyncSession, trade: Trade, exit_price: float) -> Trade:
        """Close a trade, computing ROI and PnL."""
        trade.exit_price = exit_price
        trade.exit_time = datetime.now(timezone.utc)
        trade.status = "closed"
        trade.roi = (exit_price - trade.entry_price) / trade.entry_price
        trade.pnl_usd = trade.entry_amount_usd * trade.roi
        await session.flush()
        return trade

    async def list_trades(
        self,
        session: AsyncSession,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Trade]:
        """Return a paginated list of trades, optionally filtered by status."""
        stmt = select(Trade).order_by(Trade.id.desc()).limit(limit).offset(offset)
        if status:
            stmt = stmt.where(Trade.status == status)
        res = await session.execute(stmt)
        return list(res.scalars().all())

    async def get_open(self, session: AsyncSession) -> list[Trade]:
        """Return all currently open trades."""
        res = await session.execute(
            select(Trade).where(Trade.status == "open").order_by(Trade.id.asc())
        )
        return list(res.scalars().all())

    async def get_by_id(self, session: AsyncSession, trade_id: int) -> Trade | None:
        """Return a trade by primary key, or None."""
        return await session.get(Trade, trade_id)  # type: ignore[return-value]
