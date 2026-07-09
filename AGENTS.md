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
