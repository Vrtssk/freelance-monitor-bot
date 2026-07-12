# Freelance Monitor Bot

Telegram-бот и локальная веб-доска для мониторинга фриланс-бирж. Система
собирает объявления с четырёх источников, отсеивает вакансии и посторонние темы,
уточняет релевантность через LLM и присылает подходящие заказы в Telegram.

[![Python](https://img.shields.io/badge/python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/docker_compose-ready-2496ED?logo=docker&logoColor=white)](https://docs.docker.com/compose/)
[![License](https://img.shields.io/badge/license-MIT-22c55e.svg)](LICENSE)

## Возможности

- FL.ru и Freelance.ru через HTTP/HTML.
- Weblancer и Kwork через Playwright.
- Per-user выбор тем, источников и пауза мониторинга.
- Guards для вакансий и явно посторонних задач.
- Keyword prefilter и LLM-классификация через OpenAI-compatible API/Groq.
- Keyword fallback при отключении, timeout или rate limit LLM.
- Плановый мониторинг через APScheduler и ручная команда `/check`.
- Telegram Top-5 и сырой поток последних 10 объявлений.
- PostgreSQL для хранения, дедупликации и статистики.
- Dark SaaS web dashboard с общей лентой, Top-10, статистикой, поиском,
  source-фильтрами и live-статусом циклов.

## Архитектура

```text
                  PostgreSQL
                 /          \
                /            \
  bot: aiogram + scheduler    api: FastAPI + Jinja board
             \                 /
              scrapers -> filters
```

`bot` и `api` — отдельные процессы. Только `bot` имеет экземпляр Telegram Bot и
может отправлять уведомления. Подробности: [docs/architecture.md](docs/architecture.md).

## Быстрый старт

```bash
git clone https://github.com/Vrtssk/freelance-monitor-bot.git
cd freelance-monitor-bot
cp .env.example .env
# Заполнить BOT_TOKEN и LLM_API_KEY
docker compose up -d --build
```

После запуска сайт открывается на `http://localhost:8000`, а OpenAPI UI — на
`http://localhost:8000/docs`. Полный guide по Docker, локальному запуску, backup
и VPS: [docs/operations.md](docs/operations.md).

## Команды бота

| Команда | Назначение |
|---|---|
| `/start` | главное меню |
| `/topics` | выбор тем |
| `/top` | 5 наиболее актуальных заказов по темам пользователя |
| `/recent` | последние 10 сохранённых объявлений без фильтра тем |
| `/check` | внеплановый цикл мониторинга |
| `/help` | справка |

Главное меню также содержит настройки источников, паузу, статистику,
демо-объявления и ссылку на веб-доску.

## Веб-доска

| Route | Назначение |
|---|---|
| `GET /` | последние 300 сохранённых объявлений |
| `GET /top` | Top-10 не-вакансий по relevance score |
| `GET /stats` | визуальная статистика |
| `GET /api/stats` | базовая статистика в JSON |
| `GET /api/monitor/status` | статус и время циклов |
| `POST /scrape/run` | ручной цикл из web UI/API |

Точное поведение и ограничения: [docs/web-and-api.md](docs/web-and-api.md).

## Конфигурация

| Переменная | Назначение |
|---|---|
| `BOT_TOKEN` | Telegram Bot token |
| `DATABASE_URL` | PostgreSQL async URL |
| `SCRAPE_INTERVAL` | интервал в секундах, минимум 60 |
| `SCRAPE_ENABLED` | включить плановые циклы |
| `USE_PLAYWRIGHT` | browser scraping |
| `LLM_API_KEY` | ключ LLM-провайдера |
| `LLM_BASE_URL` | OpenAI-compatible endpoint |
| `LLM_MODEL` | модель классификации |
| `LLM_ENABLED` | включить LLM-этап |
| `WEB_BASE_URL` | ссылка на сайт, которую присылает бот |
| `ALLOWED_USER_IDS` | читается конфигурацией, но доступ пока не блокирует |

Полная таблица и оговорки: [docs/operations.md](docs/operations.md).

## Фильтрация и рейтинг

Порядок: vacancy guard → off-topic guard → keyword match → LLM → keyword
fallback. Relevance учитывает отклики (`0.55`), сложность (`0.20`), свежесть
(`0.18`) и цену (`0.07`). Детали: [docs/filtering-and-ranking.md](docs/filtering-and-ranking.md).

## Тестирование

```bash
python -m pytest
# или
docker compose exec -T api python -m pytest
```

Покрыты фильтры, LLM parser/fallback, relevance, скраперы на fixtures,
форматирование, клавиатуры, source preferences, refresh и Jinja UI.

## Известные ограничения

- API не имеет встроенной авторизации. Не открывайте административные endpoints
  публично без reverse proxy/authentication.
- Web manual scrape работает без Telegram Bot и не гарантирует доставку.
- Настройки per-user, но дедупликация и `notified` пока глобальны.
- Схема использует SQLAlchemy и startup patches; Alembic пока нет.
- Topic chips на веб-доске пока визуальные и не фильтруют данные.

## Документация

- [Архитектура и модель данных](docs/architecture.md)
- [Запуск и эксплуатация](docs/operations.md)
- [Фильтрация и ранжирование](docs/filtering-and-ranking.md)
- [Веб-доска и HTTP API](docs/web-and-api.md)

## Лицензия

[MIT](LICENSE)
