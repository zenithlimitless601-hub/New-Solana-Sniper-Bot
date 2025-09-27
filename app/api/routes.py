from typing import Optional
from fastapi import APIRouter, Depends, Request, Query, WebSocket, WebSocketDisconnect
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_session
from app.analytics.service import AnalyticsService
from app.schemas import (
    TokenIn,
    AnalysisOut,
    TradeOut,
    TradeListOut,
    StatsOut,
    EquityCurveOut,
    StrategyConfigIn,
    StrategyConfigOut,
)
from app.schemas.engine import ProcessResultOut


router = APIRouter(prefix="/api/v1")


def _to_trade_out(t) -> TradeOut:
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
async def analyze_token(token: TokenIn, request: Request, session: AsyncSession = Depends(get_session)):
    analyzer = request.app.state.analyzer
    res = await analyzer.assess(token)
    return res


@router.post("/token/process", response_model=ProcessResultOut)
async def process_token(
    token: TokenIn,
    request: Request,
    session: AsyncSession = Depends(get_session),
    mode: Optional[str] = Query(None),
    amount_usd: Optional[float] = Query(None),
):
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
    amount_usd: Optional[float] = Query(None),
):
    engine = request.app.state.engine
    result = await engine.process_new_token(token, mode="simulation", amount_usd=amount_usd)
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
    amount_usd: Optional[float] = Query(None),
):
    engine = request.app.state.engine
    result = await engine.process_new_token(token, mode="real", amount_usd=amount_usd)
    return ProcessResultOut(
        token_id=result.token_id,
        opened_trade_id=result.opened_trade_id,
        analysis=result.analysis,
    )


@router.get("/trades", response_model=TradeListOut)
async def list_trades(
    request: Request,
    session: AsyncSession = Depends(get_session),
    status: Optional[str] = Query(None),
):
    engine = request.app.state.engine
    items = await engine.trade_repo.list_trades(session, status=status, limit=200)
    return TradeListOut(items=[_to_trade_out(t) for t in items], total=len(items))


@router.get("/stats", response_model=StatsOut)
async def stats(request: Request, session: AsyncSession = Depends(get_session)):
    svc = AnalyticsService(session)
    return await svc.get_stats()


@router.get("/equity", response_model=EquityCurveOut)
async def equity(request: Request, session: AsyncSession = Depends(get_session)):
    svc = AnalyticsService(session)
    return await svc.get_equity_curve()


@router.get("/strategy", response_model=StrategyConfigOut)
async def get_strategy(request: Request):
    sm = request.app.state.strategy_manager
    p = sm.params
    return StrategyConfigOut(take_profit_multipliers=p.take_profit_multipliers, stop_loss=p.stop_loss)


@router.websocket("/ws/tokens")
async def ws_tokens(websocket: WebSocket):
    app = websocket.app
    manager = app.state.ws_manager
    logger.info("WS route: accepting /ws/tokens")
    await manager.connect(websocket)
    try:
        while True:
            msg = await websocket.receive_text()
            logger.debug("WS route: received from client: {m}", m=msg)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WS route: disconnected /ws/tokens")


@router.post("/strategy", response_model=StrategyConfigOut)
async def set_strategy(cfg: StrategyConfigIn, request: Request):
    sm = request.app.state.strategy_manager
    p = sm.update(
        take_profit_multipliers=cfg.take_profit_multipliers,
        stop_loss=cfg.stop_loss,
    )
    return StrategyConfigOut(take_profit_multipliers=p.take_profit_multipliers, stop_loss=p.stop_loss)
