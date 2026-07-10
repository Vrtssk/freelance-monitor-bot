from aiogram import Router, F
from aiogram.types import CallbackQuery

from bot.keyboards import back_kb
from config.topics import SOURCES
from db.repository import count_stats
from db.session import async_session_factory

router = Router(name="stats")


@router.callback_query(F.data == "menu:stats")
async def cb_stats(callback: CallbackQuery):
    async with async_session_factory() as session:
        stats = await count_stats(session)

    by_source = stats.get("by_source") or {}
    total = stats.get("total", 0)
    notified = stats.get("notified", 0)

    src_lines = []
    for key, src in SOURCES.items():
        cnt = by_source.get(key, 0)
        src_lines.append(f"  {src['emoji']} {src['name']} — {cnt}")

    text = (
        "📊 <b>Статистика</b>\n\n"
        "<i>За всё время работы:</i>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        f"📈 Всего найдено: <b>{total}</b>\n"
        f"📩 Отправлено: <b>{notified}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>По источникам:</b>\n"
        + "\n".join(src_lines)
        + "\n\n"
        f"<i>ℹ️ Реальные данные из базы PostgreSQL.</i>"
    )
    await _edit(callback, text, back_kb())


async def _edit(callback: CallbackQuery, text: str, markup=None):
    try:
        await callback.message.edit_text(text, reply_markup=markup)
    except Exception:
        await callback.message.answer(text, reply_markup=markup)
    await callback.answer()
