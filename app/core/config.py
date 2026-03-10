"""Application configuration via environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file.

    Supports SQLite (aiosqlite) and PostgreSQL (asyncpg) backends,
    configurable trading strategy, and optional Pump.fun real-time listener.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "Solana Sniper Bot"
    database_url: str = "sqlite+aiosqlite:///./data.db"
    rpc_url: str | None = None
    rpc_ws_url: str | None = None
    rpc_http_url: str | None = None
    pumpfun_enabled: bool = False
    jupiter_base_url: str = "https://quote-api.jup.ag"
    ai_model: str = "rule"
    openai_api_key: str | None = None
    trade_mode: str = "simulation"
    price_provider: str = "mock"
    entry_amount_usd: float = 50.0
    take_profit_multipliers: list[float] = [2.0, 3.0, 5.0]
    stop_loss: float = 0.3
    risk_threshold: float = 0.6
    monitor_enabled: bool = True
    admin_username: str = "admin"
    admin_password: str = "admin"
    log_level: str = "INFO"
    log_to_file: bool = False
    log_file: str | None = None

    def model_post_init(self, __context: dict) -> None:  # type: ignore[override]
        tpm_csv = self._read_env_list("TAKE_PROFIT_MULTIPLIERS_CSV")
        if tpm_csv:
            self.take_profit_multipliers = [float(x) for x in tpm_csv]

    @staticmethod
    def _read_env_list(key: str) -> list[str] | None:
        import os

        v = os.getenv(key)
        if not v:
            return None
        return [x.strip() for x in v.split(",") if x.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()
