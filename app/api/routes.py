"""REST API and WebSocket routes for the sniper bot."""

from fastapi import APIRouter, Depends, Query, Request, WebSocket, WebSocketDisconnect
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.service import AnalyticsService
from app.core.db import get_session
from app.schemas import (
    AnalysisOut,
    EquityCurveOut,
    StatsOut,
    StrategyConfigIn,
    StrategyConfigOut,
    TokenIn,
    TradeListOut,
    TradeOut,
)
from app.schemas.engine import ProcessResultOut

router = APIRouter(prefix="/api/v1")


def _to_trade_out(t) -> TradeOut:
    """Map a Trade ORM instance to the API response schema."""
    return TradeOut(
        id=t.id,
        token_id=t.token_id,
        mode=t.mode,
        status=t.status,
        entry_price=t.entry_price,
        entry_amount_usd=t.entry_amount_usd,
        entry_time=t.entry_time,
        exit_price=t.exit_price,
        exit_time=t.exit_time,
        roi=t.roi,
        pnl_usd=t.pnl_usd,
    )


@router.post("/token/analyze", response_model=AnalysisOut)
async def analyze_token(
    token: TokenIn,
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> AnalysisOut:
    """Run risk analysis on a token without opening a trade."""
    analyzer = request.app.state.analyzer
    return await analyzer.assess(token)


@router.post("/token/process", response_model=ProcessResultOut)
async def process_token(
    token: TokenIn,
    request: Request,
    session: AsyncSession = Depends(get_session),
    mode: str | None = Query(None),
    amount_usd: float | None = Query(None),
) -> ProcessResultOut:
    """Full pipeline: analyze a token and optionally open a trade."""
    engine = request.app.state.engine
    result = await engine.process_new_token(token, mode=mode, amount_usd=amount_usd)
    return ProcessResultOut(
        token_id=result.token_id,
        opened_trade_id=result.opened_trade_id,
        analysis=result.analysis,
    )


@router.post("/simulate", response_model=ProcessResultOut)
async def simulate_trade(
    token: TokenIn,
    request: Request,
    session: AsyncSession = Depends(get_session),
    amount_usd: float | None = Query(None),
) -> ProcessResultOut:
    """Analyze a token and open a simulated (paper) trade."""
    engine = request.app.state.engine
    result = await engine.process_new_token(
        token, mode="simulation", amount_usd=amount_usd
    )
    return ProcessResultOut(
        token_id=result.token_id,
        opened_trade_id=result.opened_trade_id,
        analysis=result.analysis,
    )


@router.post("/trade", response_model=ProcessResultOut)
async def real_trade(
    token: TokenIn,
    request: Request,
    session: AsyncSession = Depends(get_session),
    amount_usd: float | None = Query(None),
) -> ProcessResultOut:
    """Analyze a token and open a real on-chain trade."""
    engine = request.app.state.engine
    result = await engine.process_new_token(
        token, mode="real", amount_usd=amount_usd
    )
    return ProcessResultOut(
        token_id=result.token_id,
        opened_trade_id=result.opened_trade_id,
        analysis=result.analysis,
    )


@router.get("/trades", response_model=TradeListOut)
async def list_trades(
    request: Request,
    session: AsyncSession = Depends(get_session),
    status: str | None = Query(None),
) -> TradeListOut:
    """List all trades with optional status filter."""
    engine = request.app.state.engine
    items = await engine.trade_repo.list_trades(session, status=status, limit=200)
    return TradeListOut(items=[_to_trade_out(t) for t in items], total=len(items))


@router.get("/stats", response_model=StatsOut)
async def stats(
    request: Request, session: AsyncSession = Depends(get_session)
) -> StatsOut:
    """Return aggregate trading statistics (ROI, win rate, drawdown)."""
    svc = AnalyticsService(session)
    return await svc.get_stats()


@router.get("/equity", response_model=EquityCurveOut)
async def equity(
    request: Request, session: AsyncSession = Depends(get_session)
) -> EquityCurveOut:
    """Return the cumulative equity curve from closed trades."""
    svc = AnalyticsService(session)
    return await svc.get_equity_curve()


@router.get("/strategy", response_model=StrategyConfigOut)
async def get_strategy(request: Request) -> StrategyConfigOut:
    """Return current strategy parameters (TP multipliers, stop-loss)."""
    sm = request.app.state.strategy_manager
    p = sm.params
    return StrategyConfigOut(
        take_profit_multipliers=p.take_profit_multipliers, stop_loss=p.stop_loss
    )


@router.post("/strategy", response_model=StrategyConfigOut)
async def set_strategy(
    cfg: StrategyConfigIn, request: Request
) -> StrategyConfigOut:
    """Update strategy parameters at runtime (no restart required)."""
    sm = request.app.state.strategy_manager
    p = sm.update(
        take_profit_multipliers=cfg.take_profit_multipliers,
        stop_loss=cfg.stop_loss,
    )
    return StrategyConfigOut(
        take_profit_multipliers=p.take_profit_multipliers, stop_loss=p.stop_loss
    )


@router.websocket("/ws/tokens")
async def ws_tokens(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time new token notifications."""
    manager = websocket.app.state.ws_manager
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
