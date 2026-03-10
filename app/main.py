"""Application factory and entrypoint for the Solana Sniper Bot."""

from fastapi import FastAPI
from loguru import logger

from app.api.routes import router as api_router
from app.core.config import get_settings
from app.core.db import async_session_factory, init_db
from app.core.logging import setup_logging
from app.core.ws import TokensWSManager
from app.services.ai.rule_based import RuleBasedAnalyzer
from app.services.pricing.mock_price import MockPriceProvider
from app.services.strategy.engine import StrategyEngine
from app.services.strategy.params import StrategyManager, StrategyParams
from app.services.trading.simulator import SimulatorTrader


def create_app() -> FastAPI:
    """Build and configure the FastAPI application with all services."""
    settings = get_settings()
    setup_logging(
        level=settings.log_level,
        log_to_file=settings.log_to_file,
        log_file=settings.log_file,
    )
    application = FastAPI(title=settings.app_name)
    application.state.settings = settings

    logger.info("Starting {name}", name=settings.app_name)
    logger.info(
        "Config: mode={mode}, entry={amt}, tp={tps}, sl={sl}, risk={thr}",
        mode=settings.trade_mode,
        amt=settings.entry_amount_usd,
        tps=settings.take_profit_multipliers,
        sl=settings.stop_loss,
        thr=settings.risk_threshold,
    )

    application.state.price_provider = MockPriceProvider()
    application.state.analyzer = RuleBasedAnalyzer()
    application.state.strategy_manager = StrategyManager(
        StrategyParams(
            take_profit_multipliers=settings.take_profit_multipliers,
            stop_loss=settings.stop_loss,
        )
    )
    application.state.trader = SimulatorTrader(
        price_provider=application.state.price_provider,
        session_factory=async_session_factory,
    )
    application.state.ws_manager = TokensWSManager()
    application.state.engine = StrategyEngine(
        session_factory=async_session_factory,
        price_provider=application.state.price_provider,
        strategy_manager=application.state.strategy_manager,
        analyzer=application.state.analyzer,
        trader=application.state.trader,
        ws_manager=application.state.ws_manager,
    )

    @application.on_event("startup")
    async def on_startup() -> None:
        await init_db()
        await application.state.engine.start()
        logger.info("Startup complete")

    application.include_router(api_router)
    return application


app = create_app()
