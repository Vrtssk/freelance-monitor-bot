from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config.sources import SCRAPE_SOURCES
from config.topics import TOPICS


def main_menu_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🔥 Топ-5 актуальных", callback_data="menu:top5")
    kb.button(text="🔄 Проверить сейчас", callback_data="menu:refresh")
    kb.button(text="📋 Последние 10", callback_data="menu:recent")
    kb.button(text="📱 Мои темы", callback_data="menu:topics")
    kb.button(text="⚙️ Настройки", callback_data="menu:settings")
    kb.button(text="📊 Статистика", callback_data="menu:stats")
    kb.button(text="🔔 Демо-объявление", callback_data="menu:demo")
    kb.button(text="ℹ️ Помощь", callback_data="menu:help")
    # Open the local web board. Sent as a clickable text link (callback), not a
    # URL button — Telegram rejects "localhost"/private URLs in inline URL buttons.
    kb.button(text="🌐 Все объявления (сайт)", callback_data="menu:board")
    kb.adjust(1, 1, 1, 2, 2, 1)
    return kb.as_markup()


def topics_kb(selected: set[str]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for topic in TOPICS:
        mark = "✅" if topic["key"] in selected else "☐"
        kb.button(
            text=f"{mark} {topic['emoji']} {topic['name']}",
            callback_data=f"toggle:{topic['key']}",
        )
    kb.button(text="✅ Готово", callback_data="menu:main")
    kb.adjust(1, 1, 1, 1, 1, 1)
    return kb.as_markup()


def back_kb(target: str = "menu:main") -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="◀️ Назад", callback_data=target)
    return kb.as_markup()


def demo_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="➡️ Следующее", callback_data="demo:next")
    kb.button(text="◀️ В меню", callback_data="menu:main")
    kb.adjust(2)
    return kb.as_markup()


def settings_kb(paused: bool, active_sources: int = 0, total_sources: int = 0) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if paused:
        kb.button(text="▶️ Возобновить", callback_data="set:toggle_monitor")
    else:
        kb.button(text="⏸ Пауза", callback_data="set:toggle_monitor")
    kb.button(text="📱 Изменить темы", callback_data="menu:topics")
    src_label = "📡 Источники"
    if total_sources:
        src_label += f" ({active_sources}/{total_sources})"
    kb.button(text=src_label, callback_data="set:sources")
    kb.button(text="🗑 Сбросить темы", callback_data="set:reset_topics")
    kb.button(text="◀️ Назад", callback_data="menu:main")
    kb.adjust(1, 1, 1, 1, 1)
    return kb.as_markup()


def sources_kb(disabled: set[str]) -> InlineKeyboardMarkup:
    """Multi-select keyboard for scrape sources.

    ✅ = enabled (will be parsed), ☐ = disabled (unchecked). Tapping toggles
    the source via ``src:toggle:<key>``.
    """
    kb = InlineKeyboardBuilder()
    for src in SCRAPE_SOURCES:
        mark = "✅" if src["key"] not in disabled else "☐"
        kb.button(
            text=f"{mark} {src['emoji']} {src['name']}",
            callback_data=f"src:toggle:{src['key']}",
        )
    kb.button(text="◀️ Назад", callback_data="menu:settings")
    kb.adjust(1, 1, 1, 1, 1)
    return kb.as_markup()
