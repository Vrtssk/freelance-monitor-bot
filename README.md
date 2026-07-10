# freelance-monitor-bot

Telegram bot (personal use) that monitors Russian & Belarusian freelance exchanges
and sends new, relevant IT job postings based on user-selected topics.

## Features

- Monitors 4 exchanges: **FL.ru**, **Freelance.ru**, **Weblancer**, **Kwork**
- Hybrid filtering: keyword pre-filter → LLM classification (Groq, OpenAI-compatible)
- Real-time Telegram notifications via inline-keyboard menus
- Topic selection (Front-end, Верстка, Парсинг, Скрипты, Чат-боты)
- PostgreSQL storage, FastAPI health/stats endpoints
- Docker Compose: `db` + `bot` + `api`
- `🔥 Топ-5 актуальных` — кнопка/команда `/top` с ранжированием по релевантности
- `📋 Последние 10` — кнопка/команда `/recent` — сырой поток последних объявлений со всех сайтов
- `🌐 Все объявления (сайт)` — URL-кнопка в меню открывает локальную доску всех собранных постов (`GET /` API, см. `docs/board.md`)

## Quick start

```bash
cp .env.example .env   # fill BOT_TOKEN, LLM_API_KEY, DATABASE_URL
docker compose up -d --build
```

Bot token: get from [@BotFather](https://t.me/BotFather).
LLM key: get from [Groq](https://console.groq.com) (model `llama-3.1-8b-instant`).

## Project layout

See `AGENTS.md` (git/commit rules, tech stack), `docs/architecture.md`
(full backend architecture), `docs/bot.md` (bot UI screens), `docs/filters.md`
(hybrid keyword + LLM classification pipeline), and `docs/top5.md`
(Топ-5 актуальных: релевантность и точки входа).

## Tests

```bash
.venv/bin/python -m pytest
```
