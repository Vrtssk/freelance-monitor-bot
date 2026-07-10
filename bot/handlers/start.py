from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery

from bot.keyboards import main_menu_kb
from config.topics import TOPICS
from db.repository import get_or_create_user, get_user_topics, is_monitoring_enabled
from db.session import async_session_factory

router = Router(name="start")

WELCOME_TEXT = (
    "🤖 <b>Привет!</b> Я бот-мониторинг фриланс-бирж.\n\n"
    "Я отслеживаю новые объявления на:\n"
    "🔵 FL.ru  ·  🟢 Freelance.ru  ·  🟡 Weblancer  ·  🟠 Kwork\n\n"
    "и присылаю тебе только релевантные — по твоим выбранным темам.\n\n"
    "👇 Выбери действие:"
)

HELP_TEXT = (
    "ℹ️ <b>Помощь</b>\n\n"
    "Я бот-мониторинг фриланс-бирж. Вот что я умею:\n\n"
    "📱 <b>Мои темы</b> — выбрать интересующие темы\n"
    "⚙️ <b>Настройки</b> — управление мониторингом\n"
    "📊 <b>Статистика</b> — статистика по объявлениям\n"
    "🔔 <b>Демо</b> — пример объявления\n\n"
    "<b>Команды:</b>\n"
    "/start — главное меню\n"
    "/topics — выбор тем\n"
    "/help — эта справка"
)


@router.message(CommandStart())
async def cmd_start(message: Message):
    tg_id = message.from_user.id
    username = message.from_user.username
    async with async_session_factory() as session:
        await get_or_create_user(session, tg_id, username)
        n = len(await get_user_topics(session, tg_id))
    extra = f"\n\n📱 Выбрано тем: <b>{n}</b> из {len(TOPICS)}" if n else ""
    await message.answer(WELCOME_TEXT + extra, reply_markup=main_menu_kb())


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(HELP_TEXT, reply_markup=main_menu_kb())


@router.callback_query(F.data == "menu:main")
async def cb_main(callback: CallbackQuery):
    uid = callback.from_user.id
    async with async_session_factory() as session:
        n = len(await get_user_topics(session, uid))
        active = await is_monitoring_enabled(session, uid)
    status = "⏸ Пауза" if not active else "✅ Активен"
    text = (
        f"🤖 <b>Главное меню</b>\n\n"
        f"📱 Тем выбрано: <b>{n}</b> из {len(TOPICS)}\n"
        f"📡 Мониторинг: {status}\n\n"
        f"👇 Выбери действие:"
    )
    await _edit(callback, text, main_menu_kb())


@router.callback_query(F.data == "menu:help")
async def cb_help(callback: CallbackQuery):
    await _edit(callback, HELP_TEXT, main_menu_kb())


async def _edit(callback: CallbackQuery, text: str, markup=None):
    try:
        await callback.message.edit_text(text, reply_markup=markup)
    except Exception:
        await callback.message.answer(text, reply_markup=markup)
    await callback.answer()
