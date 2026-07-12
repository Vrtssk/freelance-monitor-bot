# Запуск и эксплуатация

## Требования

- Docker с Compose plugin — рекомендуемый способ запуска.
- Для запуска без Docker: Python 3.11+ (основной образ — Python 3.12),
  PostgreSQL и Chromium для Playwright.

## Docker

```bash
cp .env.example .env
# Заполнить BOT_TOKEN и LLM_API_KEY
docker compose up -d --build
```

Сервисы:

- `db` — PostgreSQL 16;
- `bot` — Telegram polling, scheduler и уведомления;
- `api` — сайт/API на `http://localhost:8000`.

Полезные команды:

```bash
docker compose ps
docker compose logs -f bot api
docker compose restart bot api
docker compose down
```

## Локальный запуск

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/playwright install chromium
.venv/bin/python run.py
.venv/bin/python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

Нужен доступный PostgreSQL и корректный `DATABASE_URL`.

## Переменные окружения

| Переменная | Назначение | По умолчанию |
|---|---|---|
| `BOT_TOKEN` | токен BotFather | пусто |
| `ALLOWED_USER_IDS` | список tg-id; **сейчас читается, но доступ не блокирует** | пусто |
| `DATABASE_URL` | async SQLAlchemy URL PostgreSQL | локальный PostgreSQL |
| `SCRAPE_INTERVAL` | интервал циклов, секунды; минимум 60 | `300` |
| `SCRAPE_ENABLED` | запуск планового scraping | `true` |
| `USE_PLAYWRIGHT` | настройка browser scraping | `true` |
| `LLM_API_KEY` | ключ Groq/OpenAI-compatible API | пусто |
| `LLM_BASE_URL` | endpoint классификатора | Groq OpenAI endpoint |
| `LLM_MODEL` | модель классификации | `llama-3.1-8b-instant` |
| `LLM_ENABLED` | включить LLM после keyword prefilter | `true` |
| `USER_AGENT` | User-Agent HTTP-скраперов | Chrome-like |
| `API_HOST` | host для ручного uvicorn-запуска | `0.0.0.0` |
| `API_PORT` | port для ручного uvicorn-запуска | `8000` |
| `WEB_BASE_URL` | ссылка на сайт, которую присылает бот | `http://localhost:8000` |

В `docker-compose.yml` команда uvicorn задаёт host/port явно. `API_HOST` и
`API_PORT` используются только если команда запуска учитывает их самостоятельно.

Для открытия сайта с телефона задайте `WEB_BASE_URL` с LAN-IP, например
`http://192.168.1.50:8000`. Telegram отвергает localhost/private IP в URL-кнопках,
поэтому бот присылает обычную кликабельную текстовую ссылку через callback.

## Тестирование

```bash
python -m pytest
```

Если зависимости установлены только в Docker:

```bash
docker compose exec -T api python -m pytest
```

Покрыты фильтры, LLM parser/fallback, relevance, скраперы на fixtures,
форматирование, клавиатуры, source preferences, refresh и HTML-рендеринг.

## Диагностика скраперов

```bash
curl http://localhost:8000/scrapers
curl -X POST http://localhost:8000/scrapers/fl_ru/test
```

Тестовый endpoint не пишет результаты в БД и возвращает до 10 постов. Он, как
и ручной запуск цикла, не должен быть публично доступен.

## PostgreSQL и backup

Данные лежат в volume `pgdata`. Перед обновлением сервера делайте dump:

```bash
docker compose exec -T db pg_dump -U freelance freelance_bot > backup.sql
```

Восстановление в пустую БД:

```bash
docker compose exec -T db psql -U freelance freelance_bot < backup.sql
```

## Безопасность production

Текущий FastAPI не имеет встроенной аутентификации, rate limit и CSRF-защиты.
`POST /scrape/run` и `/scrapers/{source}/test` меняют состояние или запускают
дорогие операции. При размещении на VPS:

1. Закройте порт 8000 firewall или reverse proxy.
2. Добавьте HTTPS и внешнюю авторизацию для административных endpoint.
3. Не публикуйте `.env`, dump БД, токены и API-ключи.
4. Учитывайте глобальную дедупликацию, описанную в `architecture.md`.
