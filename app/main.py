from fastapi import FastAPI
from loguru import logger
from app.core.config import get_settings
from app.core.db import init_db, async_session_factory
from app.api.routes import router as api_router
from app.services.pricing.mock_price import MockPriceProvider
from app.services.ai.rule_based import RuleBasedAnalyzer
from app.services.trading.simulator import SimulatorTrader
from app.services.strategy.params import StrategyParams, StrategyManager
from app.services.strategy.engine import StrategyEngine
from app.core.logging import setup_logging
from app.core.ws import TokensWSManager


def create_app() -> FastAPI:
    settings = get_settings()
    setup_logging(level=settings.log_level, log_to_file=settings.log_to_file, log_file=settings.log_file)
    app = FastAPI(title=settings.app_name)

    app.state.settings = settings
    logger.info("Starting application: {name}", name=settings.app_name)
    logger.info(
        "Config: mode={mode}, entry_amount={amt}, tps={tps}, sl={sl}, risk_thr={thr}, monitor={mon}",
        mode=settings.trade_mode,
        amt=settings.entry_amount_usd,
        tps=settings.take_profit_multipliers,
        sl=settings.stop_loss,
        thr=settings.risk_threshold,
        mon=settings.monitor_enabled,
    )
    app.state.price_provider = MockPriceProvider()
    app.state.analyzer = RuleBasedAnalyzer()
    app.state.strategy_manager = StrategyManager(
        StrategyParams(
            take_profit_multipliers=settings.take_profit_multipliers,
            stop_loss=settings.stop_loss,
        )
    )
    app.state.trader = SimulatorTrader(
        price_provider=app.state.price_provider,
        session_factory=async_session_factory,
    )
    app.state.ws_manager = TokensWSManager()
    app.state.engine = StrategyEngine(
        session_factory=async_session_factory,
        price_provider=app.state.price_provider,
        strategy_manager=app.state.strategy_manager,
        analyzer=app.state.analyzer,
        trader=app.state.trader,
        ws_manager=app.state.ws_manager,
    )

    @app.on_event("startup")
    async def on_startup() -> None:
        logger.info("App startup: initializing DB and strategy engine")
        await init_db()
        await app.state.engine.start()
        logger.info("App startup complete")

    app.include_router(api_router)
    return app


app = create_app()
