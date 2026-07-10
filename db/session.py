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
]

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
