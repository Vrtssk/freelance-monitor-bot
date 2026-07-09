from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from bot.keyboards import topics_kb, back_kb
from bot.state import selected_topics
from config.topics import TOPICS, TOPIC_BY_KEY

router = Router(name="topics")

TOPICS_TEXT = (
    "📱 <b>Выбор тем</b>\n\n"
    "Отметь темы, которые тебе интересны.\n"
    "Бот будет присылать только объявления по выбранным темам.\n\n"
    "<i>Нажми на тему, чтобы включить/выключить её.</i>"
)


@router.message(Command("topics"))
async def cmd_topics(message: Message):
    await message.answer(
        TOPICS_TEXT,
        reply_markup=topics_kb(selected_topics[message.from_user.id]),
    )


@router.callback_query(F.data == "menu:topics")
async def cb_topics(callback: CallbackQuery):
    uid = callback.from_user.id
    await _edit(callback, TOPICS_TEXT, topics_kb(selected_topics[uid]))


@router.callback_query(F.data.startswith("toggle:"))
async def cb_toggle(callback: CallbackQuery):
    uid = callback.from_user.id
    key = callback.data.split(":", 1)[1]
    topics = selected_topics[uid]

    if key in topics:
        topics.discard(key)
        action = "выключена"
    else:
        topics.add(key)
        action = "включена"

    topic = TOPIC_BY_KEY.get(key)
    topic_name = f"{topic['emoji']} {topic['name']}" if topic else key

    await callback.answer(f"Тема {action}: {topic_name}", show_alert=False)
    await callback.message.edit_reply_markup(
        reply_markup=topics_kb(topics),
    )


async def _edit(callback: CallbackQuery, text: str, markup=None):
    try:
        await callback.message.edit_text(text, reply_markup=markup)
    except Exception:
        await callback.message.answer(text, reply_markup=markup)
    await callback.answer()
