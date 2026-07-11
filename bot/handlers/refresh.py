from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from bot.keyboards import main_menu_kb
from scheduler.monitor import monitor_service

router = Router(name="refresh")


def _build_result(summary: dict) -> str:
    if summary.get("skipped"):
        return (
            "⌛ Сейчас уже идёт другая проверка. "
            "Попробуй ещё раз через минуту."
        )

    sources = summary.get("sources", {})
    total_found = sum(s.get("found", 0) for s in sources.values())
    total_new = sum(s.get("new", 0) for s in sources.values())
    notified = summary.get("notified", 0)

    if total_new == 0:
        return (
            "🔄 Проверка завершена.\n"
            f"Просмотрено объявлений: {total_found}.\n"
            "Новых подходящих заказов пока нет."
        )
    return (
        "🔄 Проверка завершена!\n"
        f"Просмотрено: {total_found}, новых: {total_new}.\n"
        f"📨 Отправлено тебе: {notified}."
    )


async def _report(message: Message, summary: dict) -> None:
    await message.answer(
        _build_result(summary),
        reply_markup=main_menu_kb(),
    )


@router.message(Command("check"))
async def cmd_check(message: Message):
    """Manually trigger an immediate scrape→filter→notify cycle."""
    await message.answer("⏳ Проверяю биржи, это займёт до минуты…")
    summary = await monitor_service.run_cycle()
    await _report(message, summary)


@router.callback_query(F.data == "menu:refresh")
async def cb_refresh(callback: CallbackQuery):
    """Run an immediate monitoring cycle from the main menu button."""
    await callback.answer("⏳ Проверяю биржи…")
    summary = await monitor_service.run_cycle()
    await callback.message.answer(
        _build_result(summary),
        reply_markup=main_menu_kb(),
    )
