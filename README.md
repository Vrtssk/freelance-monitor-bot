# 🤖 Freelance Monitor Bot

> Telegram-бот для мониторинга фриланс-бирж с ИИ-фильтрацией релевантных заказов
> и локальной веб-доской всех объявлений.
>
> *Telegram bot that monitors freelance exchanges, filters relevant jobs with an
> LLM classifier, and ships a local web board of every collected posting.*

[![Python](https://img.shields.io/badge/python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/docker--compose-ready-2496ED?logo=docker&logoColor=white)](https://docs.docker.com/compose/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-73%20passing-brightgreen.svg)](#testing)

---

## ✨ Что умеет

- 🔎 **Мониторинг 4 бирж** — FL.ru, Freelance.ru, Weblancer, Kwork
  (server-rendered + headless Chromium для JS-сайтов).
- 🧠 **Гибридная фильтрация** — ключевой предфильтр → уточняющая
  классификация через LLM (Groq / OpenAI-совместимый API).
- 🎯 **Узкие темы** — Front-end, Вёрстка сайтов, Парсинг и сбор данных,
  Скрипты и автоматизация, Чат-боты / Telegram-боты.
- 🚫 **Без мусора** — автоматически отсекает вакансии/найм и заказы вне тем
  (нативные мобильные/десктоп-приложения, игры, ML-исследования и т.п.).
- 🔥 **Топ-5 актуальных** — ранжирование по релевантности (отклики,
  сложность, свежесть, цена).
- 📋 **Последние 10** — сырой поток последних пришедших объявлений со всех сайтов.
- 🔄 **Проверить сейчас** — кнопка `🔄 Проверить сейчас` и команда `/check`
  запускают внеплановый цикл мониторинга мгновенно, без ожидания интервала.
- 🌐 **Выбор бирж** — в настройках можно отключить любую биржу
  (FL.ru, Freelance.ru, Weblancer.net, Kwork.ru), и бот перестанет её парсить.
- 🌐 **Веб-доска** — красивый сайт со всеми собранными постами, фильтром по
  бирже и автообновлением.
- ⚙️ **Управление из бота** — выбор тем, пауза мониторинга, статистика.
- 🐘 **PostgreSQL** для хранения и дедупа (без повторных уведомлений).

---

## 🏗 Архитектура

```
            ┌────────────┐
  APScheduler│  Monitor   │  scrape → filter → notify
   (каждые N │  Service   │
    минут)   └─────┬──────┘
                    │
        ┌───────────┼───────────────────────┐
        ▼           ▼                        ▼
   Scrapers    HybridFilter            Telegram Bot
   (4 биржи)   keywords → LLM          (aiogram)
                   │                        │
                   ▼                        ▼
              PostgreSQL              FastAPI (health / stats / 🌐 board)
```

Поток: `APScheduler` → `monitor.run_cycle()` → скраперы → `is_post_seen`
(пропуск уже виденных) → `HybridFilter.filter_posts` (ключевые слова → LLM)
→ уведомление в Telegram → `mark_post_seen`. Подробнее в [`docs/architecture.md`](docs/architecture.md).

---

## 🧰 Технологии

| Слой | Стек |
|------|------|
| Язык | Python 3.12 |
| Бот | [aiogram](https://github.com/aiogram/aiogram) 3.x |
| API | FastAPI + Uvicorn |
| БД | PostgreSQL + SQLAlchemy 2.x (async, `asyncpg`) |
| Скрапинг | `httpx` + `beautifulsoup4` (HTML), Playwright (JS) |
| LLM | OpenAI-совместимый клиент → Groq (`llama-3.1-8b-instant`) |
| Планировщик | APScheduler |
| Инфра | Docker / docker-compose |

---

## 🚀 Быстрый старт

```bash
# 1. Клонировать
git clone https://github.com/Vrtssk/freelance-monitor-bot.git
cd freelance-monitor-bot

# 2. Заполнить переменные окружения
cp .env.example .env
#   отредактируй .env: BOT_TOKEN, LLM_API_KEY, DATABASE_URL

# 3. Поднять всё (bot + api + postgres)
docker compose up -d --build
```

Готово — бот начнёт мониторинг, а доска откроется на
**http://localhost:8000**.

### Команды бота

| Команда | Назначение |
|---------|------------|
| `/start` | главное меню |
| `/top` | 🔥 Топ-5 актуальных объявлений |
| `/recent` | 📋 Последние 10 объявлений |
| `/check` | 🔄 Внеплановая проверка бирж прямо сейчас |
| `/topics` | выбор тем |
| `/help` | справка |

---

## ⚙️ Конфигурация (`.env`)

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `BOT_TOKEN` | токен от [@BotFather](https://t.me/BotFather) | — |
| `LLM_API_KEY` | ключ Groq (или любого OpenAI-совместимого API) | — |
| `LLM_BASE_URL` | базовый URL LLM-провайдера | `https://api.groq.com/openai/v1` |
| `LLM_MODEL` | модель классификации | `llama-3.1-8b-instant` |
| `DATABASE_URL` | строка подключения к Postgres | `postgresql+asyncpg://...` |
| `SCRAPE_INTERVAL` | период цикла мониторинга, сек | `300` |
| `SCRAPE_ENABLED` | вкл/выкл скрапинг | `true` |
| `USE_PLAYWRIGHT` | использовать headless-браузер для JS-сайтов | `true` |
| `WEB_BASE_URL` | базовый URL веб-доски (для кнопки в боте) | `http://localhost:8000` |
| `ALLOWED_USER_IDS` | ограничить доступ списком tg-id (через запятую) | *(все)* |

---

## 🔎 Как работает фильтрация

Два этапа, чтобы не платить за LLM за заведомо нерелевантное:

1. **Ключевой предфильтр** (`filters/keywords.py`) — быстро отсекает по
   ключевым словам выбранных тем.
2. **LLM-классификация** (`filters/llm.py`) — уточняет, релевантен ли заказ
   и к каким темам относится.

Дополнительно две детерминированные «воронки» отсекают ложные срабатывания:

- `filters/vacancy.py` — выбрасывает вакансии/найм (собеседования, «в штат»,
  оклад…).
- `filters/off_topic.py` — выбрасывает заказы вне тем (нативные моб./десктоп-
  приложения, игры), даже если они случайно зацепились за слово «верстка».

Подробнее — в [`docs/filters.md`](docs/filters.md).

---

## 🖥 Веб-доска

Локальный сайт со всеми собранными объявлениями: тёмная тема, карточки
(источник, бюджет, темы, описание, дата), фильтр по бирже и автообновление.
Открывается кнопкой `🌐 Все объявления (сайт)` в меню бота (приходит
кликабельная ссылка, т.к. Telegram не принимает `localhost` в URL-кнопках).

Две страницы с навигацией вверху:

- `GET /` — 🗂 все объявления;
- `GET /top` — 🔥 топ-10 самых релевантных заказов (ранжирование по откликам,
  свежести, сложности и цене; вакансии исключены), с бейджем релевантности.
- `GET /stats` — визуальная статистика по базе и источникам;
- `GET /api/stats` — та же базовая статистика в JSON для интеграций.

В sidebar отображаются фактическое время последнего завершённого цикла и
обратный отсчёт до следующей проверки. Кнопка «Запустить» вызывает
`POST /scrape/run` и показывает результат прямо на странице.

---

## 🧪 Тестирование

```bash
python -m pytest
```

Покрыты фильтры (ключевой + LLM-парсер + вакансии + off-topic), скраперы
(на сохранённых HTML-фикстурах), форматирование уведомлений и доски,
ранжирование релевантности и клавиатуры. Конфигурация тестов — в `pytest.ini`.

---

## 📂 Структура проекта

```
api/          FastAPI: health, stats, GET / (веб-доска)
bot/          aiogram: handlers, keyboards, main
config/       настройки (pydantic), темы и источники
db/           SQLAlchemy-модели, сессия, миграции, репозиторий
filters/      keywords → llm → vacancy → off_topic (pipeline)
models/       нормализованная схема JobPosting
scrapers/     base + fl_ru, freelance_ru, weblancer, kwork
scheduler/    APScheduler: monitor (scrape→filter→notify), manager
utils/        relevance (ранжирование), formatting (уведомления/доска)
docs/         architecture, bot, filters, top5, board
tests/        зеркало структуры + фикстуры
```

---

## 🗺 Возможные улучшения

- Мультиязычность / мультипользователь (сейчас заточено под одного владельца).
- Кнопка «отметить прочитанным / скрыть» прямо в уведомлении.
- Дополнительные биржи и Telegram-каналы как источники.
- Деплой-гайд (VPS) и CI (GitHub Actions) с прогоном тестов.

---

## 📄 Лицензия

Проект распространяется под [MIT](LICENSE).

## 👤 Автор

Сделано как личный инструмент мониторинга фриланс-бирж и выложено как
портфолио-проект. Предложения и PR приветствуются.
