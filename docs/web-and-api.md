# Веб-доска и HTTP API

## Стек

Сайт рендерится FastAPI/Jinja2 без отдельной frontend-сборки. HTMX обновляет
card-grid, Alpine.js хранит source filter, Tailwind Play CDN и custom CSS задают
оформление. Шрифты Manrope и Roboto Mono загружаются через Google Fonts.

CDN-зависимости означают, что без интернета базовый HTML откроется, но внешние
скрипты/шрифты могут быть недоступны.

## HTML-страницы

| Route | Поведение |
|---|---|
| `GET /` | последние 300 сохранённых постов, newest first |
| `GET /top?limit=10` | рейтинг не-вакансий, максимум 500 кандидатов |
| `GET /stats` | визуальная статистика базы и источников |

`GET /?partial=1&src=<key>` и `/top?partial=1&src=<key>` возвращают только
`partials/grid.html` для HTMX swap.

### Реально работающие элементы

- server-side фильтр по источнику;
- глобальный и локальный client-side поиск по тексту уже загруженных карточек;
- `Ctrl/Cmd + K` фокусирует поиск;
- автообновление grid каждые 90 секунд;
- визуальный переключатель grid/masonry-класса;
- live countdown по последнему `ScrapeRun` и `SCRAPE_INTERVAL`;
- ручной вызов `POST /scrape/run` с результатом на странице;
- responsive grid: 4/3/2/1 колонки и нижняя навигация вместо sidebar.

Кнопки тем сейчас являются визуальными placeholders и не фильтруют данные.
Настоящей masonry-библиотеки, pagination/infinite scroll, budget/new/relevance
фильтров и сохранения UI-настроек в Local Storage нет.

### Карточки

Карточка содержит источник, title, description, topics, бюджет, отклики, дату и
действия. «Открыть» ведёт на объявление, «Источник» — на главную биржи. В `/top`
показывается SVG relevance ring. Вакансии отмечаются отдельно.

## JSON и служебные routes

| Method | Route | Назначение |
|---|---|---|
| `GET` | `/health` | scrape/LLM health flags |
| `GET` | `/api/stats` | total, notified и counts по источникам |
| `GET` | `/api/monitor/status` | running, interval, last/next timestamps |
| `POST` | `/scrape/run` | ручной цикл и summary |
| `GET` | `/scrapers` | зарегистрированные скраперы |
| `POST` | `/scrapers/{source}/test` | test fetch без записи в БД |

FastAPI также предоставляет `/docs`, `/redoc` и `/openapi.json`.

## Значения статистики

- `total` — число строк `seen_posts`.
- `notified` — число глобальных постов с `notified=True`.
- `vacancies` — записи с `is_vacancy=True`.
- `fresh_24` — посты, впервые увиденные за последние 24 часа.
- `avg_price` — среднее `price_value` для постов с числовой ценой.
- `sources_enabled` в текущей реализации — число разных источников,
  представленных в БД, а не конфигурация включённых бирж.

## Ручной запуск и безопасность

API-процесс не содержит Telegram Bot. Ручной web-запуск способен получить и
сохранить объявления, но не доставить уведомления. Endpoint не имеет встроенной
авторизации и предназначен для доверенной локальной сети. Рекомендации по VPS —
в [operations.md](operations.md).
