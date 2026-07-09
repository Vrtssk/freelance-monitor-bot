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

- Python 3.11+, `aiogram` 3.x (Telegram bot)
- `httpx` + `beautifulsoup4` for server-rendered scrapers (FL.ru, Freelance.ru)
- `playwright` for JS-rendered scrapers (Weblancer.net, Kwork.ru)
- `aiosqlite` for storage (seen posts, user settings, selected topics)
- `openai` (OpenAI-compatible) for LLM classification of postings
- `docker` / `docker-compose` for running the bot
- Filtering: **hybrid** — keyword pre-filter then LLM classification

## Scraping targets

| Site | Render | Scraper approach |
|------|--------|-----------------|
| FL.ru | server | httpx + BeautifulSoup, JSON-LD ItemList |
| Freelance.ru | server | httpx + BeautifulSoup, `.task-card` |
| Weblancer.net | Next.js JS | Playwright headless |
| Kwork.ru | JS | Playwright headless |
| Хабр Фриланс | — | CLOSED (410), excluded |

## Topics (user-selected, IT / Разработка)

- 🖥 Front-end
- 🔨 Верстка сайтов
- 🕷 Парсинг и сбор данных
- ⚙️ Скрипты и автоматизация
- 🤖 Чат-боты
