from aiogram import Router, F
from aiogram.types import CallbackQuery

from bot.keyboards import settings_kb
from config.settings import settings
from config.topics import TOPICS
from db.repository import (
    clear_user_topics,
    get_or_create_user,
    get_user_topics,
    is_monitoring_enabled,
    set_monitoring,
)
from db.session import async_session_factory

router = Router(name="settings")


async def _render(callback: CallbackQuery, uid: int) -> None:
    async with async_session_factory() as session:
        paused = not await is_monitoring_enabled(session, uid)
        n = len(await get_user_topics(session, uid))
    status = "⏸ <b>Пауза</b>" if paused else "✅ <b>Активен</b>"
    interval = max(60, settings.SCRAPE_INTERVAL) // 60
    text = (
        "⚙️ <b>Настройки</b>\n\n"
        f"📡 Мониторинг: {status}\n"
        f"📱 Выбрано тем: <b>{n}</b> из {len(TOPICS)}\n"
        f"🔄 Частота проверки: каждые {interval} мин\n\n"
        f"👇 Что настроить?"
    )
    await callback.message.edit_text(text, reply_markup=settings_kb(paused))


@router.callback_query(F.data == "menu:settings")
async def cb_settings(callback: CallbackQuery):
    await _render(callback, callback.from_user.id)
    await callback.answer()


@router.callback_query(F.data == "set:toggle_monitor")
async def cb_toggle_monitor(callback: CallbackQuery):
    uid = callback.from_user.id
    async with async_session_factory() as session:
        await get_or_create_user(session, uid, callback.from_user.username)
        current = await is_monitoring_enabled(session, uid)
        now_active = await set_monitoring(session, uid, not current)
    if current:
        await callback.answer("⏸ Мониторинг на паузе", show_alert=True)
    else:
        await callback.answer("▶️ Мониторинг возобновлён", show_alert=True)
    await _render(callback, uid)


@router.callback_query(F.data == "set:reset_topics")
async def cb_reset_topics(callback: CallbackQuery):
    uid = callback.from_user.id
    async with async_session_factory() as session:
        await get_or_create_user(session, uid, callback.from_user.username)
        await clear_user_topics(session, uid)
    await callback.answer("🗑 Все темы сброшены", show_alert=True)
    await _render(callback, uid)
