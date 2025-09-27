import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from app.core.config import get_settings
from app.models import Token
from app.repositories.analysis_repo import AnalysisRepo
from app.repositories.token_repo import TokenRepo
from app.repositories.trade_repo import TradeRepo
from app.schemas.token import TokenIn
from app.services.ai.base import Analyzer
from app.services.pricing.base import PriceProvider
from app.services.strategy.params import StrategyManager
from app.services.trading.base import Trader

from app.core.ws import TokensWSManager
from app.services.pumpfun.listener import PumpfunListener, PumpToken


@dataclass
class ProcessResult:
    token_id: int
    opened_trade_id: int | None
    analysis: dict[str, Any]


class StrategyEngine:
    def __init__(
        self,
        session_factory,
        price_provider: PriceProvider,
        strategy_manager: StrategyManager,
        analyzer: Analyzer,
        trader: Trader,
        ws_manager: TokensWSManager | None = None,
    ) -> None:
        self.session_factory = session_factory
        self.price_provider = price_provider
        self.strategy_manager = strategy_manager
        self.analyzer = analyzer
        self.trader = trader
        self.ws_manager = ws_manager
        self.settings = get_settings()
        self._tasks: list[asyncio.Task] = []
        self.token_repo = TokenRepo()
        self.analysis_repo = AnalysisRepo()
        self.trade_repo = TradeRepo()
        self._pump_task: asyncio.Task | None = None

    async def start(self) -> None:
        logger.info(
            "Engine.start: monitor_enabled={mon}, pumpfun_enabled={pf}, ws={ws}, http={http}",
            mon=self.settings.monitor_enabled,
            pf=self.settings.pumpfun_enabled,
            ws=self.settings.rpc_ws_url,
            http=self.settings.rpc_http_url,
        )
        if self.settings.monitor_enabled:
            logger.info("Engine: starting mock token feed")
            self._tasks.append(asyncio.create_task(self._mock_token_feed()))
        self._tasks.append(asyncio.create_task(self._monitor_open_trades()))
        if self.settings.pumpfun_enabled and self.settings.rpc_ws_url and self.settings.rpc_http_url:
            logger.info(
                "Engine: starting Pumpfun listener ws={ws} http={http}",
                ws=self.settings.rpc_ws_url,
                http=self.settings.rpc_http_url,
            )
            self._pump_task = asyncio.create_task(self._run_pump_listener())

    async def _mock_token_feed(self) -> None:
        while True:
            await asyncio.sleep(10)
            token = TokenIn(
                address=f"MOCK-{int(asyncio.get_running_loop().time())}",
                symbol="MOCK",
                name="Mock Token",
                extras={"twitter": "https://twitter.com/mock"},
            )
            try:
                await self.process_new_token(token)
            except Exception:
                pass

    @asynccontextmanager
    async def _session(self) -> AsyncSession:
        async with self.session_factory() as session:
            async with session.begin():
                yield session

    async def process_new_token(self, token_in: TokenIn, mode: str | None = None, amount_usd: float | None = None) -> ProcessResult:
        logger.info("process_new_token: address={addr}", addr=token_in.address)
        analysis = await self.analyzer.assess(token_in)
        logger.debug("analysis result: score={s}, is_scam={sc}", s=analysis.score, sc=analysis.is_scam)
        async with self._session() as session:
            token, created = await self.token_repo.create_or_update(session, token_in.model_dump())
            logger.info("token persisted: id={id}, created={cr}", id=token.id, cr=created)
            await self.analysis_repo.create(
                session,
                {
                    "token_id": token.id,
                    "score": analysis.score,
                    "is_scam": analysis.is_scam,
                    "details": analysis.details or {},
                },
            )
            opened_trade_id = None
            if analysis.score >= self.settings.risk_threshold:
                price = await self.price_provider.get_price(token.address)
                trade = await self.trader.buy(
                    session=session,
                    token_id=token.id,
                    mode=(mode or self.settings.trade_mode),
                    entry_price=price,
                    amount_usd=(amount_usd if amount_usd is not None else self.settings.entry_amount_usd),
                )
                opened_trade_id = trade.id
            if created and self.ws_manager:
                payload = {
                    "id": token.id,
                    "address": token.address,
                    "symbol": token.symbol,
                    "name": token.name,
                    "liquidity": token.liquidity,
                    "volume_24h": token.volume_24h,
                    "created_at": token.created_at.isoformat() if getattr(token, "created_at", None) else None,
                }
                logger.info(
                    "broadcasting new token: id={id}, conns={c}",
                    id=token.id,
                    c=(self.ws_manager.connections_count() if hasattr(self.ws_manager, 'connections_count') else None),
                )
                await self.ws_manager.broadcast_new_token(payload)
        return ProcessResult(
            token_id=token.id,
            opened_trade_id=opened_trade_id,
            analysis={"score": analysis.score, "is_scam": analysis.is_scam},
        )

    async def _run_pump_listener(self) -> None:
        logger.info("Pumpfun listener: starting")
        listener = PumpfunListener(self.settings.rpc_ws_url, self.settings.rpc_http_url)  # type: ignore[arg-type]
        try:
            await listener.run(self._on_pump_token)
        except Exception as e:
            logger.exception("Pumpfun listener stopped with error: {e}", e=e)

    async def _on_pump_token(self, tok: PumpToken) -> None:
        logger.info("Pumpfun token detected: mint={m}", m=tok.mint)
        token_in = TokenIn(address=tok.mint)
        try:
            await self.process_new_token(token_in)
        except Exception:
            logger.exception("process_new_token failed for mint={m}", m=tok.mint)

    async def _monitor_open_trades(self) -> None:
        while True:
            await asyncio.sleep(3)
            async with self.session_factory() as session:
                async with session.begin():
                    trades = await self.trade_repo.get_open(session)
                    for tr in trades:
                        address = await self._token_address(session, tr.token_id)
                        price = await self.price_provider.get_price(address)
                        await self._maybe_close(session, tr, price)

    async def _token_address(self, session: AsyncSession, token_id: int) -> str:
        tok = await session.get(Token, token_id)  # type: ignore
        return tok.address  # type: ignore

    async def _maybe_close(self, session: AsyncSession, tr, price: float) -> None:
        params = self.strategy_manager.params
        tps = sorted(params.take_profit_multipliers)
        for m in reversed(tps):
            if price >= tr.entry_price * m:
                await self.trader.sell(session, tr, price)
                return
        if price <= tr.entry_price * (1 - params.stop_loss):
            await self.trader.sell(session, tr, price)
