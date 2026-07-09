from aiogram import Router, F
from aiogram.types import CallbackQuery

from bot.keyboards import back_kb
from config.topics import SOURCES, TOPICS

router = Router(name="stats")

STATS_TEXT = (
    "📊 <b>Статистика</b>\n\n"
    "<i>За всё время работы:</i>\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "📈 Всего найдено: <b>127</b>\n"
    "✅ Релевантных: <b>34</b>\n"
    "📩 Отправлено: <b>28</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━\n\n"
    "<b>По источникам:</b>\n"
    "  🔵 FL.ru — 45 (12 релев.)\n"
    "  🟢 Freelance.ru — 38 (9 релев.)\n"
    "  🟡 Weblancer — 28 (8 релев.)\n"
    "  🟠 Kwork — 16 (5 релев.)\n\n"
    "<b>По темам:</b>\n"
    "  🖥 Front-end — 8\n"
    "  🔨 Верстка — 6\n"
    "  🕷 Парсинг — 10\n"
    "  ⚙️ Скрипты — 5\n"
    "  🤖 Чат-боты — 5\n\n"
    f"<i>ℹ️ Данные тестовые — реальная статистика появится после запуска парсеров.</i>"
)


@router.callback_query(F.data == "menu:stats")
async def cb_stats(callback: CallbackQuery):
    await _edit(callback, STATS_TEXT, back_kb())


async def _edit(callback: CallbackQuery, text: str, markup=None):
    try:
        await callback.message.edit_text(text, reply_markup=markup)
    except Exception:
        await callback.message.answer(text, reply_markup=markup)
    await callback.answer()
