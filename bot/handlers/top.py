from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from bot.keyboards import back_kb, main_menu_kb
from db.repository import get_top_relevant
from db.session import async_session_factory
from datetime import datetime, timezone
from utils.formatting import format_top_list
from utils.relevance import age_hours_from, compute_relevance

router = Router(name="top")

_TOP_LIMIT = 5


async def _build_top(telegram_id: int) -> list[tuple]:
    async with async_session_factory() as session:
        rows = await get_top_relevant(session, telegram_id, limit=50)
    now = datetime.now(timezone.utc)
    scored = []
    for row in rows:
        age = age_hours_from(now, row.published_at, row.seen_at)
        score = compute_relevance(
            responses=row.responses or 0,
            age_hours=age,
            complexity=row.complexity or 3,
            price=row.price_value,
        )
        scored.append((row, score))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:_TOP_LIMIT]


@router.message(Command("top"))
async def cmd_top(message: Message):
    items = await _build_top(message.from_user.id)
    await message.answer(format_top_list(items), reply_markup=main_menu_kb())


@router.callback_query(F.data == "menu:top5")
async def cb_top5(callback: CallbackQuery):
    items = await _build_top(callback.from_user.id)
    await _edit(callback, format_top_list(items), back_kb())


async def _edit(callback: CallbackQuery, text: str, markup=None):
    try:
        await callback.message.edit_text(text, reply_markup=markup)
    except Exception:
        await callback.message.answer(text, reply_markup=markup)
    await callback.answer()
