from aiogram import Router, F
from aiogram.types import CallbackQuery

from bot.keyboards import settings_kb
from bot.state import selected_topics, monitoring_active
from config.topics import TOPICS

router = Router(name="settings")


@router.callback_query(F.data == "menu:settings")
async def cb_settings(callback: CallbackQuery):
    uid = callback.from_user.id
    paused = not monitoring_active.get(uid, True)
    n = len(selected_topics[uid])
    status = "⏸ <b>Пауза</b>" if paused else "✅ <b>Активен</b>"

    text = (
        "⚙️ <b>Настройки</b>\n\n"
        f"📡 Мониторинг: {status}\n"
        f"📱 Выбрано тем: <b>{n}</b> из {len(TOPICS)}\n"
        f"🔄 Частота проверки: каждые 5 минут\n\n"
        f"👇 Что настроить?"
    )
    await _edit(callback, text, settings_kb(paused))


@router.callback_query(F.data == "set:toggle_monitor")
async def cb_toggle_monitor(callback: CallbackQuery):
    uid = callback.from_user.id
    current = monitoring_active.get(uid, True)
    monitoring_active[uid] = not current

    if current:
        await callback.answer("⏸ Мониторинг на паузе", show_alert=True)
    else:
        await callback.answer("▶️ Мониторинг возобновлён", show_alert=True)

    paused = not monitoring_active[uid]
    n = len(selected_topics[uid])
    status = "⏸ <b>Пауза</b>" if paused else "✅ <b>Активен</b>"
    text = (
        "⚙️ <b>Настройки</b>\n\n"
        f"📡 Мониторинг: {status}\n"
        f"📱 Выбрано тем: <b>{n}</b> из {len(TOPICS)}\n"
        f"🔄 Частота проверки: каждые 5 минут\n\n"
        f"👇 Что настроить?"
    )
    await callback.message.edit_text(text, reply_markup=settings_kb(paused))


@router.callback_query(F.data == "set:reset_topics")
async def cb_reset_topics(callback: CallbackQuery):
    uid = callback.from_user.id
    selected_topics[uid].clear()
    await callback.answer("🗑 Все темы сброшены", show_alert=True)
    await cb_settings(callback)


async def _edit(callback: CallbackQuery, text: str, markup=None):
    try:
        await callback.message.edit_text(text, reply_markup=markup)
    except Exception:
        await callback.message.answer(text, reply_markup=markup)
    await callback.answer()
