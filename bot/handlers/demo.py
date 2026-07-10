from aiogram import Router, F
from aiogram.types import CallbackQuery

from bot.keyboards import demo_kb, back_kb
from config.topics import DEMO_POSTS, TOPIC_BY_KEY, SOURCES

router = Router(name="demo")

# In-memory per-user demo navigation index (visual preview only).
demo_index: dict[int, int] = {}


def format_post(post: dict, index: int, total: int) -> str:
    topic = TOPIC_BY_KEY.get(post["topic_key"])
    topic_label = f"{topic['emoji']} {topic['name']}" if topic else "—"

    src = SOURCES.get(post["source"], {})
    src_emoji = src.get("emoji", "")
    src_name = src.get("name", post["source"])

    return (
        f"🆕 <b>Новое объявление</b>  <i>({index + 1}/{total})</i>\n\n"
        f"<b>{post['title']}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🏷 <b>Тема:</b> {topic_label}\n"
        f"💰 <b>Бюджет:</b> {post['budget']}\n"
        f"📍 <b>Источник:</b> {src_emoji} {src_name}\n"
        f"⏱ <b>Опубликовано:</b> {post['published_ago']}\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{post['description']}\n\n"
        f"🔗 <a href=\"{post['url']}\">Открыть на {src_name}</a>"
    )


@router.callback_query(F.data == "menu:demo")
async def cb_demo(callback: CallbackQuery):
    uid = callback.from_user.id
    idx = demo_index.get(uid, 0) % len(DEMO_POSTS)
    post = DEMO_POSTS[idx]
    text = format_post(post, idx, len(DEMO_POSTS))
    await _edit(callback, text, demo_kb())


@router.callback_query(F.data == "demo:next")
async def cb_demo_next(callback: CallbackQuery):
    uid = callback.from_user.id
    idx = (demo_index.get(uid, 0) + 1) % len(DEMO_POSTS)
    demo_index[uid] = idx
    post = DEMO_POSTS[idx]
    text = format_post(post, idx, len(DEMO_POSTS))
    await _edit(callback, text, demo_kb())


async def _edit(callback: CallbackQuery, text: str, markup=None):
    try:
        await callback.message.edit_text(text, reply_markup=markup)
    except Exception:
        await callback.message.answer(text, reply_markup=markup)
    await callback.answer()
