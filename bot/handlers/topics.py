from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from bot.keyboards import topics_kb, back_kb
from config.topics import TOPICS, TOPIC_BY_KEY
from db.repository import (
    get_or_create_user,
    get_user_topics,
    set_user_topic,
)
from db.session import async_session_factory

router = Router(name="topics")

TOPICS_TEXT = (
    "📱 <b>Выбор тем</b>\n\n"
    "Отметь темы, которые тебе интересны.\n"
    "Бот будет присылать только объявления по выбранным темам.\n\n"
    "<i>Нажми на тему, чтобы включить/выключить её.</i>"
)


@router.message(Command("topics"))
async def cmd_topics(message: Message):
    uid = message.from_user.id
    async with async_session_factory() as session:
        selected = await get_user_topics(session, uid)
    await message.answer(TOPICS_TEXT, reply_markup=topics_kb(selected))


@router.callback_query(F.data == "menu:topics")
async def cb_topics(callback: CallbackQuery):
    uid = callback.from_user.id
    async with async_session_factory() as session:
        selected = await get_user_topics(session, uid)
    await _edit(callback, TOPICS_TEXT, topics_kb(selected))


@router.callback_query(F.data.startswith("toggle:"))
async def cb_toggle(callback: CallbackQuery):
    uid = callback.from_user.id
    key = callback.data.split(":", 1)[1]
    async with async_session_factory() as session:
        await get_or_create_user(session, uid, callback.from_user.username)
        selected = await get_user_topics(session, uid)
        enabled = key not in selected
        selected = await set_user_topic(session, uid, key, enabled)
        action = "включена" if enabled else "выключена"

    topic = TOPIC_BY_KEY.get(key)
    topic_name = f"{topic['emoji']} {topic['name']}" if topic else key
    await callback.answer(f"Тема {action}: {topic_name}", show_alert=False)
    await callback.message.edit_reply_markup(reply_markup=topics_kb(selected))


async def _edit(callback: CallbackQuery, text: str, markup=None):
    try:
        await callback.message.edit_text(text, reply_markup=markup)
    except Exception:
        await callback.message.answer(text, reply_markup=markup)
    await callback.answer()
