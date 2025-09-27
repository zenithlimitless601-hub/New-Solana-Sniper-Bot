from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Trade
from app.schemas.stats import StatsOut, EquityCurveOut, EquityPoint


class AnalyticsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _closed_trades(self) -> list[Trade]:
        res = await self.session.execute(
            select(Trade).where(Trade.status == "closed").order_by(Trade.exit_time.asc())
        )
        return list(res.scalars().all())

    async def get_stats(self) -> StatsOut:
        trades = await self._closed_trades()
        if not trades:
            return StatsOut(total_roi=0.0, win_rate=0.0, avg_profit_usd=0.0, max_drawdown=0.0)
        total_entry = sum(t.entry_amount_usd for t in trades)
        total_pnl = sum((t.pnl_usd or 0.0) for t in trades)
        total_roi = (total_pnl / total_entry) if total_entry else 0.0
        wins = sum(1 for t in trades if (t.pnl_usd or 0.0) > 0)
        win_rate = wins / len(trades)
        avg_profit = total_pnl / len(trades)
        equity = 0.0
        peak = 0.0
        max_dd = 0.0
        for t in trades:
            equity += t.pnl_usd or 0.0
            if equity > peak:
                peak = equity
            drawdown = (peak - equity) / peak if peak > 0 else 0.0
            if drawdown > max_dd:
                max_dd = drawdown
        return StatsOut(
            total_roi=round(total_roi, 6),
            win_rate=round(win_rate, 6),
            avg_profit_usd=round(avg_profit, 6),
            max_drawdown=round(max_dd, 6),
        )

    async def get_equity_curve(self) -> EquityCurveOut:
        trades = await self._closed_trades()
        points: list[EquityPoint] = []
        equity = 0.0
        for t in trades:
            equity += t.pnl_usd or 0.0
            ts = t.exit_time or t.entry_time
            points.append(EquityPoint(t=ts, equity=round(equity, 6)))
        return EquityCurveOut(points=points)
