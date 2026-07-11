"""Available freelance exchanges the bot can scrape.

Each entry is a scraping source the user can enable/disable individually
from the bot's settings. ``ALL_SOURCE_KEYS`` is the canonical ordered list
used to build scraper sets and the in-bot source picker.
"""

SCRAPE_SOURCES = [
    {"key": "fl_ru", "name": "FL.ru", "emoji": "🟦"},
    {"key": "freelance_ru", "name": "Freelance.ru", "emoji": "🟩"},
    {"key": "weblancer", "name": "Weblancer.net", "emoji": "🟧"},
    {"key": "kwork", "name": "Kwork.ru", "emoji": "🟪"},
]

ALL_SOURCE_KEYS = [s["key"] for s in SCRAPE_SOURCES]
