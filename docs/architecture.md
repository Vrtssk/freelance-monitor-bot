# Архитектура бэкенда

Полный бэкенд бота: FastAPI + PostgreSQL + парсеры + гибридная фильтрация.

## Компоненты

### 1. Модель данных (`db/models.py`)
- `User` — пользователь Telegram (`telegram_id`, `monitoring_enabled`).
- `UserTopic` — выбранные темы пользователя (`topic_key`).
- `SeenPost` — уже обработанные объявления (дедуп по `source`+`external_id`).
- `ScrapeRun` — лог циклов парсинга (статистика/отладка).

Таблицы создаются через `db.session.init_db()` (async, `Base.metadata.create_all`).

### 2. Репозиторий (`db/repository.py`)
Все обращения к БД через `async_session_factory`. Функции:
`get_or_create_user`, `get_user_topics`, `set_user_topic`, `clear_user_topics`,
`set_monitoring`, `is_monitoring_enabled`, `get_active_subscribers`,
`is_post_seen`, `mark_post_seen`, `count_stats`.

> Важно: темы читаются прямым запросом к таблице `UserTopic`, а не через
> relationship `user.topics`, чтобы избежать устаревания кэша identity-map
> после вставки новой строки в той же сессии.

### 3. Парсеры (`scrapers/`)
Базовый класс `BaseScraper` (загрузка HTML через `httpx`, общие заголовки).
Конкретные:
- `fl_ru.py` — FL.ru: HTML `.b-post` + JSON-LD `ItemList`.
- `freelance_ru.py` — Freelance.ru: `<article class="task-card">`, категория `c[]=4`.
- `weblancer.py` — Weblancer: Playwright (Next.js), категория `veb-programmirovanie-31`.
- `kwork.py` — Kwork: Playwright + фолбэк на API-endpoint.

Каждый парсер возвращает список `JobPosting(source, external_id, title, ...)`.

### 4. Фильтрация (`filters/`)
- `keywords.py` — `match_keywords(post, topic_keys)`: быстрый матч по
  ключевым словам тем (`config/topics.py`).
- `llm.py` — `LLMClassifier.classify()`: запрос к OpenRouter/DeepSeek
  (OpenAI-совместимый API), возвращает `{relevant, subtopics, reason}` в JSON.
- `pipeline.py` — `HybridFilter`: сначала keyword-префильтр, затем LLM
  для кандидатов.

### 5. Пайплайн мониторинга (`scheduler/monitor.py`)
`MonitorService.run_cycle()`:
1. Для каждого парсера: `fetch()` → новые посты (`is_post_seen` пропуск).
2. Для каждого активного подписчика: `filter_posts(posts, user_topics)`.
3. Совпавшие → `bot.send_message` → `mark_post_seen(notified=True)`.
4. Остальные новые посты → `mark_post_seen(notified=False)`.

### 6. Планировщик (`scheduler/manager.py`)
`start_scheduler()` запускает APScheduler с интервалом `SCRAPE_INTERVAL`
(в секундах, минимум 60). Один инстанс за раз (`max_instances=1`).

### 7. API (`api/main.py`)
FastAPI со lifespan-инициализацией БД:
- `GET /health` — статус + флаги scrape/llm.
- `GET /stats` — статистика из БД.
- `POST /scrape/run` — ручной запуск цикла.
- `GET /scrapers` — список источников.
- `POST /scrapers/{source}/test` — тест парсера (без записи в БД).

### 8. Бот (`bot/`)
`bot/main.py` при старте: `init_db()` → `monitor_service.set_bot(bot)` →
`start_scheduler()` → long-polling. Хендлеры (`bot/handlers/`) работают с БД
через `db.repository`, форматирование уведомлений — `utils/formatting.py`.

## Запуск (Docker)
```bash
cp .env.example .env   # заполнить BOT_TOKEN, LLM_API_KEY, DATABASE_URL
docker compose up -d --build
```
Сервисы: `db` (postgres:16), `bot`, `api` (порт 8000).

## Локальная разработка без Docker
Требуется PostgreSQL. Установить зависимости:
```bash
python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python run.py        # бот + scheduler
.venv/bin/python -m uvicorn api.main:app --port 8000  # API
```
Playwright-браузер: `playwright install chromium` (нужен для Weblancer/Kwork).
