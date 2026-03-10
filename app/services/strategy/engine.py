"""Core strategy engine -- orchestrates token analysis, trading and monitoring."""

import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import get_settings
from app.core.ws import TokensWSManager
from app.models import Token
from app.repositories.analysis_repo import AnalysisRepo
from app.repositories.token_repo import TokenRepo
from app.repositories.trade_repo import TradeRepo
from app.schemas.token import TokenIn
from app.services.ai.base import Analyzer
from app.services.pricing.base import PriceProvider
from app.services.pumpfun.listener import PumpToken, PumpfunListener
from app.services.strategy.params import StrategyManager
from app.services.trading.base import Trader


@dataclass
class ProcessResult:
    """Result of processing a new token through the pipeline."""

    token_id: int
    opened_trade_id: int | None
    analysis: dict[str, Any]


class StrategyEngine:
    """Orchestrates the full trading pipeline.

    Responsibilities:
        - Accepts new tokens (via API or Pump.fun listener)
        - Runs risk analysis through the configured Analyzer
        - Opens trades when score >= risk_threshold
        - Monitors open trades and auto-closes on TP/SL hit
        - Broadcasts new tokens to WebSocket clients
    """

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
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
        """Start background tasks: mock feed, trade monitor, Pump.fun listener."""
        logger.info(
            "Engine.start: monitor_enabled={mon}, pumpfun_enabled={pf}",
            mon=self.settings.monitor_enabled,
            pf=self.settings.pumpfun_enabled,
        )
        if self.settings.monitor_enabled:
            self._tasks.append(asyncio.create_task(self._mock_token_feed()))
        self._tasks.append(asyncio.create_task(self._monitor_open_trades()))
        if (
            self.settings.pumpfun_enabled
            and self.settings.rpc_ws_url
            and self.settings.rpc_http_url
        ):
            logger.info("Engine: starting Pumpfun listener")
            self._pump_task = asyncio.create_task(self._run_pump_listener())

    async def _mock_token_feed(self) -> None:
        """Generate a fake token every 10 seconds for testing."""
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
    async def _session(self):
        async with self.session_factory() as session:
            async with session.begin():
                yield session

    async def process_new_token(
        self,
        token_in: TokenIn,
        mode: str | None = None,
        amount_usd: float | None = None,
    ) -> ProcessResult:
        """Full pipeline: analyze token, persist, optionally open trade.

        Args:
            token_in: Token data from the API or listener.
            mode: Override trade mode ('simulation' or 'real').
            amount_usd: Override entry amount in USD.

        Returns:
            ProcessResult with token_id, trade_id (if opened), and analysis.
        """
        logger.info("process_new_token: address={addr}", addr=token_in.address)
        analysis = await self.analyzer.assess(token_in)

        async with self._session() as session:
            token, created = await self.token_repo.create_or_update(
                session, token_in.model_dump()
            )
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
                    mode=mode or self.settings.trade_mode,
                    entry_price=price,
                    amount_usd=(
                        amount_usd
                        if amount_usd is not None
                        else self.settings.entry_amount_usd
                    ),
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
                    "created_at": (
                        token.created_at.isoformat()
                        if getattr(token, "created_at", None)
                        else None
                    ),
                }
                await self.ws_manager.broadcast_new_token(payload)

        return ProcessResult(
            token_id=token.id,
            opened_trade_id=opened_trade_id,
            analysis={"score": analysis.score, "is_scam": analysis.is_scam},
        )

    async def _run_pump_listener(self) -> None:
        """Run the Pump.fun logsSubscribe listener with auto-reconnect."""
        listener = PumpfunListener(
            self.settings.rpc_ws_url,  # type: ignore[arg-type]
            self.settings.rpc_http_url,  # type: ignore[arg-type]
        )
        try:
            await listener.run(self._on_pump_token)
        except Exception as e:
            logger.exception("Pumpfun listener stopped: {e}", e=e)

    async def _on_pump_token(self, tok: PumpToken) -> None:
        """Callback for each new Pump.fun token mint."""
        logger.info("Pumpfun token detected: mint={m}", m=tok.mint)
        try:
            await self.process_new_token(TokenIn(address=tok.mint))
        except Exception:
            logger.exception("process_new_token failed for mint={m}", m=tok.mint)

    async def _monitor_open_trades(self) -> None:
        """Periodically check open trades against TP/SL thresholds."""
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
        """Look up a token's on-chain address by its database ID."""
        tok = await session.get(Token, token_id)
        return tok.address  # type: ignore[union-attr]

    async def _maybe_close(
        self, session: AsyncSession, tr, price: float
    ) -> None:
        """Close a trade if any take-profit or stop-loss level is hit."""
        params = self.strategy_manager.params
        tps = sorted(params.take_profit_multipliers)
        for m in reversed(tps):
            if price >= tr.entry_price * m:
                await self.trader.sell(session, tr, price)
                return
        if price <= tr.entry_price * (1 - params.stop_loss):
            await self.trader.sell(session, tr, price)
