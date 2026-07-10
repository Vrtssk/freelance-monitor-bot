# AGENTS.md

Project instructions for AI agents working on this repo.

## Repository

- **Remote:** `git@github.com:Vrtssk/freelance-monitor-bot.git` (private)
- **Hosting:** local Docker first, then a VPS/server.

## Git workflow (MANDATORY RULE)

After every meaningful change to this project, you MUST:
1. Commit the changes with a clear, conventional commit message (Russian or English, concise).
2. Push the commit to the `main` branch of the `origin` remote.

Never leave changes uncommitted/unpushed at the end of a task. If a push fails
(e.g. network, auth), retry once and report the issue to the user.

Do NOT commit secrets: `.env`, API keys, tokens. These must stay in `.env` only
(which is gitignored).

## Documentation rule (MANDATORY)

Every meaningful module, package, and public function MUST be documented in a
human-readable way:

1. For code: use clear, descriptive names and write concise docstrings on every
   public function/class summarizing **what** it does and **why**.
2. For any non-trivial logic, design decision, or architecture choice, create or
   update a Markdown (`.md`) file under the relevant directory explaining it in
   Russian or English. Examples: `docs/scrapers.md`, `docs/filters.md`.
3. README.md must stay up to date with how to run, configure, and extend the bot.

## Testing rule (MANDATORY)

All non-trivial logic MUST be covered by automated tests:

1. Tests live in `tests/` mirroring the package layout (e.g. `tests/test_filters.py`).
2. Use `pytest` as the test runner.
3. Cover at least: filters (keyword + LLM), scrapers (HTML parsing with saved
   fixtures), formatters, and the topic/classification logic.
4. Before pushing, run `pytest` and ensure it is green.
5. Add `pytest` and `pytest-asyncio` to `requirements.txt`.

## Tech stack

- Python 3.12 (Docker: `python:3.12-slim`), works on 3.11+
- `aiogram` 3.x — Telegram bot
- `fastapi` + `uvicorn` — HTTP API (health, stats, manual scrape)
- `sqlalchemy` 2.x async + `asyncpg` — PostgreSQL storage
- `httpx` + `beautifulsoup4` — server-rendered scrapers (FL.ru, Freelance.ru)
- `playwright` (headless Chromium) — JS-rendered scrapers (Weblancer.net, Kwork.ru)
- `openai` (OpenAI-compatible) — LLM classification via OpenRouter / DeepSeek
- `apscheduler` — periodic scrape cycle
- `docker` / `docker-compose` — postgres + bot + api services
- Filtering: **hybrid** — keyword pre-filter then LLM classification

## Architecture

```
api/        FastAPI app (health, /stats, POST /scrape/run, /scrapers/{src}/test)
bot/        aiogram bot: handlers, keyboards, main entry (db + scheduler + monitor)
config/     settings (pydantic), topics (keywords, sources, demo)
db/         sqlalchemy models, async session, repository (users/topics/posts/stats)
filters/    keywords.py, llm.py (OpenRouter), pipeline.py (hybrid)
models/     JobPosting schema (normalized posting)
scrapers/   base + fl_ru, freelance_ru, weblancer, kwork
scheduler/  monitor.py (scrape→filter→notify), manager.py (APScheduler)
utils/      formatting.py (Telegram HTML notification)
```

Flow: APScheduler → `monitor.run_cycle()` → scrapers fetch → `is_post_seen`
skip → `HybridFilter.filter_posts` (keywords → LLM) → notify user via bot
→ `mark_post_seen(notified=...)`.

See `docs/architecture.md` for details.

## Scraping targets

| Site | Render | Scraper approach |
|------|--------|-----------------|
| FL.ru | server | httpx + BeautifulSoup, JSON-LD ItemList + `.b-post` |
| Freelance.ru | server | httpx + BeautifulSoup, `<article class="task-card">` |
| Weblancer.net | Next.js JS | Playwright headless, category `veb-programmirovanie-31` |
| Kwork.ru | JS | Playwright headless (+ API fallback) |
| Хабр Фриланс | — | CLOSED (410), excluded |

## LLM classification

OpenRouter-compatible endpoint. Configured via `.env`:
- `LLM_BASE_URL=https://openrouter.ai/api/v1`
- `LLM_MODEL=deepseek/deepseek-v4-flash:free`
- `LLM_API_KEY=sk-or-...`

## Topics (user-selected, IT / Разработка)

- 🖥 Front-end
- 🔨 Верстка сайтов
- 🕷 Парсинг и сбор данных
- ⚙️ Скрипты и автоматизация
- 🤖 Чат-боты
