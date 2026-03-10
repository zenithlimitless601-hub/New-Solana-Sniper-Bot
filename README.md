# Solana Sniper Bot

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Async Solana token sniper bot with real-time Pump.fun monitoring, rule-based token analysis, configurable take-profit/stop-loss strategy, and full trade simulation.

## Disclaimer

> **This software is provided for educational and research purposes only.**
>
> - Do NOT use this bot with real funds unless you fully understand the risks.
> - Cryptocurrency trading involves substantial risk of loss.
> - The authors are not responsible for any financial losses.
> - This is NOT financial advice.

## Features

- **Real-time Pump.fun listener** -- detects new token mints via Solana `logsSubscribe` RPC
- **Rule-based token analyzer** -- scam detection, risk scoring
- **Configurable strategy** -- multiple take-profit levels (x2, x3, x5), stop-loss
- **Trade simulation** -- paper trading mode with full PnL tracking
- **Analytics dashboard** -- equity curve, win rate, ROI, max drawdown
- **WebSocket feed** -- real-time new token notifications
- **REST API** -- full control via `/api/v1/` endpoints
- **Docker ready** -- single `docker compose up` deployment

## Architecture

```
app/
  api/            # FastAPI routes (REST + WebSocket)
  core/           # Config, DB, logging, WS manager
  models/         # SQLModel ORM (Token, Analysis, Trade)
  repositories/   # Data access layer
  schemas/        # Pydantic request/response models
  services/
    ai/           # Token analyzers (rule-based, OpenAI)
    pricing/      # Price providers (mock, live)
    pumpfun/      # Pump.fun logsSubscribe listener
    strategy/     # Strategy engine, params
    trading/      # Trade executor (simulator)
  analytics/      # Stats, equity curve
```

## Quick Start

### Local

```bash
git clone https://github.com/mazamaka/Solana-Sniper-Bot.git
cd Solana-Sniper-Bot

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env with your settings

uvicorn app.main:app --reload
```

API docs: http://127.0.0.1:8000/docs

### Docker

```bash
cp .env.example .env
docker compose up --build
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./data.db` | Database connection string (SQLite or PostgreSQL) |
| `RPC_WS_URL` | -- | Solana WebSocket RPC endpoint |
| `RPC_HTTP_URL` | -- | Solana HTTP RPC endpoint |
| `PUMPFUN_ENABLED` | `false` | Enable real-time Pump.fun listener |
| `MONITOR_ENABLED` | `false` | Enable mock token feed (for testing) |
| `TRADE_MODE` | `simulation` | `simulation` or `real` |
| `ENTRY_AMOUNT_USD` | `50` | Entry amount per trade in USD |
| `TAKE_PROFIT_MULTIPLIERS_CSV` | `2.0,3.0,5.0` | Take-profit levels (comma-separated) |
| `STOP_LOSS` | `0.3` | Stop-loss threshold (0.3 = -30%) |
| `RISK_THRESHOLD` | `0.6` | Minimum analysis score to open trade |
| `AI_MODEL` | `rule` | Analyzer backend (`rule` or `openai`) |
| `OPENAI_API_KEY` | -- | OpenAI API key (if `AI_MODEL=openai`) |
| `LOG_LEVEL` | `INFO` | Logging level |
| `ADMIN_USERNAME` | `admin` | Admin panel username |
| `ADMIN_PASSWORD` | `admin` | Admin panel password |

> **Note:** Public Solana RPC endpoints may rate-limit `logsSubscribe`. For production use, consider paid RPC providers (Helius, QuickNode, Chainstack, etc.).

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/token/analyze` | Analyze a token (risk score) |
| `POST` | `/api/v1/token/process` | Full pipeline: analyze + trade |
| `POST` | `/api/v1/simulate` | Paper trade a token |
| `POST` | `/api/v1/trade` | Real trade a token |
| `GET` | `/api/v1/trades` | List all trades |
| `GET` | `/api/v1/stats` | Trading statistics |
| `GET` | `/api/v1/equity` | Equity curve |
| `GET/POST` | `/api/v1/strategy` | Get/update strategy params |
| `WS` | `/api/v1/ws/tokens` | Real-time new token feed |

## Tech Stack

- **Python 3.11+** / **FastAPI** / **Uvicorn**
- **SQLModel** + **SQLAlchemy** (async) + **aiosqlite** / **asyncpg**
- **Pydantic Settings** for configuration
- **websockets** for Solana RPC subscription
- **httpx** for async HTTP
- **Loguru** for structured logging
- **Docker** + **Docker Compose**

## License

MIT

## Author

**Maksym Babenko**

- GitHub: [@mazamaka](https://github.com/mazamaka)
- Telegram: [@Mazamaka](https://t.me/Mazamaka)
