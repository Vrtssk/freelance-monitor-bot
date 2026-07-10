# freelance-monitor-bot

Telegram bot (personal use) that monitors Russian & Belarusian freelance exchanges
and sends new, relevant IT job postings based on user-selected topics.

## Features

- Monitors 4 exchanges: **FL.ru**, **Freelance.ru**, **Weblancer**, **Kwork**
- Hybrid filtering: keyword pre-filter → LLM classification (OpenRouter / DeepSeek)
- Real-time Telegram notifications via inline-keyboard menus
- Topic selection (Front-end, Верстка, Парсинг, Скрипты, Чат-боты)
- PostgreSQL storage, FastAPI health/stats endpoints
- Docker Compose: `db` + `bot` + `api`

## Quick start

```bash
cp .env.example .env   # fill BOT_TOKEN, LLM_API_KEY, DATABASE_URL
docker compose up -d --build
```

Bot token: get from [@BotFather](https://t.me/BotFather).
LLM key: get from [OpenRouter](https://openrouter.ai) (model `deepseek/deepseek-v4-flash:free`).

## Project layout

See `AGENTS.md` (git/commit rules, tech stack) and `docs/architecture.md`
(full backend architecture) and `docs/bot.md` (bot UI screens).

## Tests

```bash
.venv/bin/python -m pytest
```
