# Solana Sniper Bot

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com/)
[![SQLModel](https://img.shields.io/badge/SQLModel-async-blueviolet.svg)](https://sqlmodel.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Async Solana token sniper bot with real-time **Pump.fun** monitoring, rule-based token analysis, configurable take-profit/stop-loss strategy engine, and full trade simulation with analytics.

---

## Disclaimer

> **This software is provided for educational and research purposes only.**
>
> - Do **NOT** use this bot with real funds unless you fully understand the risks.
> - Cryptocurrency trading involves substantial risk of loss.
> - The authors are not responsible for any financial losses.
> - This is **NOT** financial advice.

---

## Features

- **Real-time Pump.fun listener** -- detects new token mints via Solana `logsSubscribe` RPC
- **Rule-based token analyzer** -- scam detection, social presence scoring, risk assessment
- **Configurable strategy** -- multiple take-profit levels (x2, x3, x5), adjustable stop-loss
- **Trade simulation** -- paper trading mode with full PnL tracking and ROI calculation
- **Analytics dashboard** -- equity curve, win rate, total ROI, max drawdown
- **WebSocket feed** -- real-time new token notifications with backlog replay
- **REST API** -- full control via `/api/v1/` endpoints with Swagger docs
- **Hot-reload strategy** -- update TP/SL parameters at runtime without restart
- **Docker ready** -- single `docker compose up` deployment
- **Pluggable architecture** -- swap analyzers, price providers, and trade executors via interfaces

---

## Architecture

```
app/
  main.py               # Application factory (FastAPI)
  api/
    routes.py            # REST + WebSocket endpoints
  core/
    config.py            # Pydantic Settings (env-based config)
    db.py                # SQLAlchemy async engine and session
    logging.py           # Loguru setup
    ws.py                # WebSocket manager with backlog
  models/
    token.py             # Token ORM (SQLModel)
    analysis.py          # Analysis ORM
    trade.py             # Trade ORM
  repositories/          # Data access layer (CRUD)
  schemas/               # Pydantic request/response models
  services/
    ai/
      base.py            # Analyzer interface (ABC)
      rule_based.py      # Heuristic scoring engine
    pricing/
      base.py            # PriceProvider interface (ABC)
      mock_price.py      # Random-walk price simulator
    pumpfun/
      listener.py        # Solana logsSubscribe listener
    strategy/
      engine.py          # Core strategy engine (orchestrator)
      params.py          # TP/SL parameters and runtime manager
    trading/
      base.py            # Trader interface (ABC)
      simulator.py       # Paper trading executor
  analytics/
    service.py           # Stats computation (ROI, drawdown, equity)
ws_monitor.py            # Standalone WS client for monitoring
```

---

## Quick Start

### Local Development

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

API docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### Docker

```bash
git clone https://github.com/mazamaka/Solana-Sniper-Bot.git
cd Solana-Sniper-Bot

cp .env.example .env
docker compose up --build
```

The API will be available at `http://localhost:8000`

### WebSocket Monitor

```bash
python ws_monitor.py
```

Connects to the bot and prints new token events in real-time.

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./data.db` | Database connection (SQLite or PostgreSQL) |
| `RPC_WS_URL` | -- | Solana WebSocket RPC endpoint |
| `RPC_HTTP_URL` | -- | Solana HTTP RPC endpoint |
| `PUMPFUN_ENABLED` | `false` | Enable real-time Pump.fun listener |
| `MONITOR_ENABLED` | `false` | Enable mock token feed (testing) |
| `TRADE_MODE` | `simulation` | `simulation` or `real` |
| `ENTRY_AMOUNT_USD` | `50` | Entry amount per trade in USD |
| `TAKE_PROFIT_MULTIPLIERS_CSV` | `2.0,3.0,5.0` | Take-profit levels (comma-separated) |
| `STOP_LOSS` | `0.3` | Stop-loss threshold (0.3 = -30%) |
| `RISK_THRESHOLD` | `0.6` | Minimum analysis score to open trade |
| `AI_MODEL` | `rule` | Analyzer backend (`rule` or `openai`) |
| `LOG_LEVEL` | `INFO` | Logging level |

> **Note:** Public Solana RPC endpoints may rate-limit `logsSubscribe`. For production use, consider paid RPC providers (Helius, QuickNode, Chainstack).

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/token/analyze` | Analyze a token (risk score, scam detection) |
| `POST` | `/api/v1/token/process` | Full pipeline: analyze + conditionally trade |
| `POST` | `/api/v1/simulate` | Paper trade a token |
| `POST` | `/api/v1/trade` | Real trade a token |
| `GET` | `/api/v1/trades` | List all trades (filterable by status) |
| `GET` | `/api/v1/stats` | Trading statistics (ROI, win rate, drawdown) |
| `GET` | `/api/v1/equity` | Equity curve data points |
| `GET` | `/api/v1/strategy` | Get current strategy parameters |
| `POST` | `/api/v1/strategy` | Update strategy parameters at runtime |
| `WS` | `/api/v1/ws/tokens` | Real-time new token feed |

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| **Language** | Python 3.11+ |
| **Web Framework** | FastAPI + Uvicorn |
| **ORM** | SQLModel + SQLAlchemy (async) |
| **Database** | SQLite (aiosqlite) / PostgreSQL (asyncpg) |
| **Configuration** | Pydantic Settings |
| **WebSocket** | websockets (Solana RPC), FastAPI WS (clients) |
| **HTTP Client** | httpx (async) |
| **Logging** | Loguru |
| **Containerization** | Docker + Docker Compose |

---

## Design Decisions

- **Interface-driven architecture**: All core services (Analyzer, PriceProvider, Trader) are defined as abstract base classes, making it easy to swap implementations.
- **Repository pattern**: Data access is encapsulated in repository classes, keeping business logic clean.
- **Hot-reloadable strategy**: TP/SL parameters can be changed via API without restarting the application.
- **WebSocket backlog**: Late-connecting clients receive recent token events from a ring buffer.

---

## License

[MIT](LICENSE)

---

## Author

**Maksym Babenko**

- GitHub: [@mazamaka](https://github.com/mazamaka)
- Telegram: [@Mazamaka](https://t.me/Mazamaka)
