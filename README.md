# Solana Sniper Bot

Минимальный MVP: API для симуляций, хранение сделок, базовая стратегия (TP x2/x3/x5 и стоп-лосс), аналитика.

## Быстрый старт (локально)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API: http://127.0.0.1:8000/docs

## Docker

```bash
docker compose up --build
```

## Env

Смотри `.env.example`. По умолчанию SQLite. Для Postgres укажи `DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/solana`.
