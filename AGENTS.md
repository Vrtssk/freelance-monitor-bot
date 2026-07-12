# AGENTS.md

Project instructions for AI agents working on this repo.

## Repository

- **Remote:** `git@github.com:Vrtssk/freelance-monitor-bot.git` (public)
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
   Russian or English.
3. README.md must stay up to date with how to run, configure, and extend the bot.
4. Canonical docs are `docs/architecture.md`, `docs/operations.md`,
   `docs/filtering-and-ranking.md`, and `docs/web-and-api.md`. Update one of
   these instead of creating overlapping feature/design documents.

## Testing rule (MANDATORY)

All non-trivial logic MUST be covered by automated tests:

1. Tests live in `tests/` mirroring the package layout (e.g. `tests/test_filters.py`).
2. Use `pytest` as the test runner.
3. Cover at least: filters (keyword + LLM), scrapers (HTML parsing with saved
   fixtures), formatters, and the topic/classification logic.
4. Before pushing, run `pytest` and ensure it is green.
5. Add `pytest` and `pytest-asyncio` to `requirements.txt`.

## Library / SDK reference rule (MANDATORY)

Whenever you work with a library, framework, SDK, API, or CLI tool, you MUST
consult the **Context7 MCP server** for current documentation BEFORE writing or
modifying any integration code (even for well-known libraries). Steps:

1. Call `resolve-library-id` with the library name to find the Context7 ID
   (format `/org/project`). Prefer High/Medium source reputation and higher
   benchmark score.
2. Call `query-docs` with that ID and a single, focused question (one concept
   per call; make a separate call per distinct concept).
3. Use the fetched docs. Do not use web search for library docs when Context7
   suffices. Use Context7 for: API syntax, config, version migration, library
   debugging, and setup — NOT for refactoring, business logic, or general
   programming concepts.

## Tech stack

- Python 3.12 (Docker: `python:3.12-slim`), works on 3.11+
- `aiogram` 3.x — Telegram bot
- `fastapi` + `uvicorn` + Jinja2/HTMX/Alpine — HTTP API and web board
- `sqlalchemy` 2.x async + `asyncpg` — PostgreSQL storage
- `httpx` + `beautifulsoup4` — server-rendered scrapers (FL.ru, Freelance.ru)
- `playwright` (headless Chromium) — JS-rendered scrapers (Weblancer.net, Kwork.ru)
- `openai` (OpenAI-compatible) — LLM classification via Groq (was OpenRouter)
- `apscheduler` — periodic scrape cycle
- `docker` / `docker-compose` — postgres + bot + api services
- Filtering: guards → keyword pre-filter → LLM classification/fallback

## Architecture

```
api/        FastAPI JSON API + server-rendered board context
bot/        aiogram bot: handlers, keyboards, main entry (db + scheduler + monitor)
config/     settings (pydantic), topics (keywords, sources, demo)
db/         SQLAlchemy models, async session, repository
filters/    vacancy/off-topic guards, keywords, LLM, hybrid pipeline
models/     JobPosting schema (normalized posting)
scrapers/   base + fl_ru, freelance_ru, weblancer, kwork
scheduler/  monitor.py (scrape→filter→notify), manager.py (APScheduler)
templates/  Jinja pages for board, top, stats and HTMX grid partial
utils/      Telegram formatting and relevance ranking
```

Flow: APScheduler → `monitor.run_cycle()` → selected scrapers → global seen skip
→ per-user sources/topics → guards → keywords → LLM/fallback → Telegram notify
→ global `seen_posts` storage.

See `docs/architecture.md` for process/data-model details. Routes and security
caveats are in `docs/web-and-api.md`; do not duplicate them here.

## Canonical docs

- `docs/architecture.md` — processes, data model, multi-user semantics.
- `docs/operations.md` — setup, environment, testing, deployment/security.
- `docs/filtering-and-ranking.md` — topic keys, pipeline, LLM, relevance.
- `docs/web-and-api.md` — HTML pages, API routes and implemented UI behavior.
