TOPICS: list[dict] = [
    {
        "key": "frontend",
        "emoji": "🖥",
        "name": "Front-end",
        "keywords": [
            "front-end", "frontend", "react", "vue", "angular", "svelte",
            "javascript", "typescript", "js ", "ts ", "фронтенд", "фронт-энд",
            "spa", "next.js", "nuxt", "redux", "webpack", "vite",
        ],
    },
    {
        "key": "markup",
        "emoji": "🔨",
        "name": "Верстка сайтов",
        "keywords": [
            "верстка", "вёрстка", "html", "css", "адаптивная верстка",
            "markup", "лэндинг", "лендинг", "figma", "макет", "bootstrap",
            "tailwind", "pixel perfect", "кроссбраузерная",
        ],
    },
    {
        "key": "parsing",
        "emoji": "🕷",
        "name": "Парсинг и сбор данных",
        "keywords": [
            "парсинг", "parsing", "scraper", "скрапинг", "сбор данных",
            "data scraping", "scrapy", "beautifulsoup", "selenium",
            "crawler", "грабер", "парсер",
        ],
    },
    {
        "key": "scripts",
        "emoji": "⚙️",
        "name": "Скрипты и автоматизация",
        "keywords": [
            "скрипт", "script", "автоматизация", "automation",
            "selenium", "puppeteer", "python скрипт", "cron",
            "расписание", "батник", "powershell", "powershell скрипт",
        ],
    },
    {
        "key": "chatbots",
        "emoji": "🤖",
        "name": "Чат-боты",
        "keywords": [
            "бот", "bot", "чат-бот", "chatbot", "telegram bot",
            "телеграм бот", "discord bot", "aiogram", "telegraf",
            "python-telegram-bot", "slack bot", "whatsapp bot",
        ],
    },
]

TOPIC_BY_KEY: dict[str, dict] = {t["key"]: t for t in TOPICS}

SOURCES = {
    "fl_ru": {"name": "FL.ru", "emoji": "🔵", "url": "https://www.fl.ru"},
    "freelance_ru": {"name": "Freelance.ru", "emoji": "🟢", "url": "https://freelance.ru"},
    "weblancer": {"name": "Weblancer", "emoji": "🟡", "url": "https://www.weblancer.net"},
    "kwork": {"name": "Kwork", "emoji": "🟠", "url": "https://kwork.ru"},
}

DEMO_POSTS: list[dict] = [
    {
        "title": "Разработка SPA на React + TypeScript",
        "topic_key": "frontend",
        "budget": "80 000 ₽",
        "source": "fl_ru",
        "url": "https://www.fl.ru/projects/5513086/nujno-pomenyat-vrstku-gotovogo-lendinga.html",
        "published_ago": "3 минуты назад",
        "description": (
            "Нужно разработать SPA-приложение на React 18 + TypeScript.\n\n"
            "Требования:\n"
            "— Интеграция с REST API\n"
            "— Адаптивный дизайн (мобилки + десктоп)\n"
            "— Темная/светлая тема\n"
            "— Оптимизация производительности\n\n"
            "Макеты в Figma. Срок — 3 недели."
        ),
    },
    {
        "title": "Адаптивная верстка лендинга по Figma-макету",
        "topic_key": "markup",
        "budget": "15 000 ₽",
        "source": "freelance_ru",
        "url": "https://freelance.ru/task/view/4873",
        "published_ago": "7 минут назад",
        "description": (
            "Требуется сверстать одностраничный лендинг по готовому макету в Figma.\n\n"
            "Требования:\n"
            "— Pixel Perfect\n"
            "— Полностью адаптивный (320px – 1920px)\n"
            "— Кроссбраузерная верстка\n"
            "— Анимации по скроллу (AOS)\n"
            "— Чистый HTML/CSS, без фреймворков\n\n"
            "Макет пришлю в личку. Бюджет обсуждаем."
        ),
    },
    {
        "title": "Парсинг каталога товаров с маркетплейса",
        "topic_key": "parsing",
        "budget": "25 000 ₽",
        "source": "weblancer",
        "url": "https://www.weblancer.net/jobs/parsing/",
        "published_ago": "12 минут назад",
        "description": (
            "Нужно написать парсер для сбора каталога товаров с маркетплейса "
            "(Ozon / Wildberries).\n\n"
            "Что собирать:\n"
            "— Название, цена, артикул, фото\n"
            "— Характеристики и отзывы\n"
            "— Выгрузка в Excel/CSV\n\n"
            "Обход капчи и блокировок. Прокси свои. "
            "Нужен скрипт на Python (Scrapy/BS4)."
        ),
    },
    {
        "title": "Автоматизация выгрузки отчетов в Google Sheets",
        "topic_key": "scripts",
        "budget": "12 000 ₽",
        "source": "kwork",
        "url": "https://kwork.ru/projects/",
        "published_ago": "20 минут назад",
        "description": (
            "Нужен скрипт на Python для автоматизации рутины:\n\n"
            "— Сбор данных из 3-х источников (API + парсинг)\n"
            "— Обработка и фильтрация\n"
            "— Выгрузка в Google Sheets по расписанию (раз в день)\n"
            "— Уведомление в Telegram о результате\n\n"
            "Скрипт должен работать на сервере (Linux). "
            "Настройка cron/systemd."
        ),
    },
    {
        "title": "Telegram-бот для интернет-магазина",
        "topic_key": "chatbots",
        "budget": "35 000 ₽",
        "source": "fl_ru",
        "url": "https://www.fl.ru/projects/5513049/sozdat-prostogo-chat-bota-v-salebot.html",
        "published_ago": "31 минуту назад",
        "description": (
            "Нужен Telegram-бот для интернет-магазина косметики.\n\n"
            "Функционал:\n"
            "— Каталог товаров с фото и ценами\n"
            "— Корзина и оформление заказа\n"
            "— Интеграция с CRM (Bitrix24)\n"
            "— Оплата через ЮKassa\n"
            "— Рассылки по подписчикам\n"
            "— Админ-панель (товары, заказы)\n\n"
            "Стек: Python + aiogram. Срок — 2 недели."
        ),
    },
]
