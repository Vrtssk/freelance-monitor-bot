from collections.abc import AsyncGenerator
import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config.settings import settings
from db.models import Base

# Columns added after the table already existed. create_all() does not ALTER
# existing tables, so apply them explicitly (idempotent via IF NOT EXISTS).
_MIGRATIONS = [
    "ALTER TABLE seen_posts ADD COLUMN IF NOT EXISTS published_at TIMESTAMPTZ",
    "ALTER TABLE seen_posts ADD COLUMN IF NOT EXISTS responses INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE seen_posts ADD COLUMN IF NOT EXISTS complexity INTEGER",
    "ALTER TABLE seen_posts ADD COLUMN IF NOT EXISTS price_value INTEGER",
    "ALTER TABLE seen_posts ADD COLUMN IF NOT EXISTS is_vacancy BOOLEAN NOT NULL DEFAULT FALSE",
]

# Vacancy / hiring (найм) markers, mirrored from filters/vacancy.py. Used once
# to backfill the is_vacancy flag on rows that were already stored before the
# column existed, so stale vacancies drop out of the Топ-5 immediately.
_VACANCY_LIKE = [
    "%собеседован%", "%ваканси%", "%трудоустро%", "%полная занятост%",
    "%неполная занятост%", "%частичная занятост%", "%график работ%",
    "%гибкий график%", "%сменный график%", "%оклад%", "%заработная плата%",
    "%з/п%", "% в штат%", "%на постоянную работу%", "%постоянную работу%",
    "%прием на работу%", "%приём на работу%", "%полный день%",
]
_VACANCY_BACKFILL = (
    "UPDATE seen_posts SET is_vacancy = TRUE WHERE is_vacancy = FALSE AND ("
    + " OR ".join(
        f"lower(COALESCE(title,'')) || ' ' || lower(COALESCE(description,'')) "
        f"LIKE '{p}'"
        for p in _VACANCY_LIKE
    )
    + ")"
)

engine = create_async_engine(settings.DATABASE_URL, echo=False, pool_pre_ping=True)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session


async def init_db() -> None:
    """Create tables if they do not exist, then apply column migrations."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        for stmt in _MIGRATIONS:
            try:
                await conn.execute(text(stmt))
            except Exception as exc:  # pragma: no cover - defensive
                logging.warning("migration skipped: %s (%s)", stmt, exc)
        # One-time backfill of the vacancy flag on already-stored rows.
        try:
            await conn.execute(text(_VACANCY_BACKFILL))
        except Exception as exc:  # pragma: no cover - defensive
            logging.warning("vacancy backfill skipped: %s", exc)
