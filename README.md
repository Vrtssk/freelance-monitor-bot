# freelance-monitor-bot

Telegram bot (personal use) that monitors Russian & Belarusian freelance exchanges
and sends new, relevant job postings based on user-selected IT topics.

## Features

- Monitors multiple freelance exchanges (FL.ru, Freelance.ru, Weblancer.net, Kwork.ru)
- Hybrid filtering: keyword pre-filter → LLM classification
- Real-time Telegram notifications
- Topic selection via inline keyboards
- Runs in Docker

## Setup

```bash
cp .env.example .env   # fill in BOT_TOKEN, LLM_*, etc.
docker compose up -d --build
```

## Project layout

See `AGENTS.md` for the full convention and git workflow.
