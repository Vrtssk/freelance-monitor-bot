from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from config.sources import ALL_SOURCE_KEYS
from db.models import ScrapeRun, SeenPost, User, UserDisabledSource, UserTopic
from filters.vacancy import is_vacancy as detect_vacancy
from models.schemas import JobPosting


async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    username: str | None = None,
) -> User:
    result = await session.execute(
        select(User).options(selectinload(User.topics)).where(User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()
    if user:
        if username and user.username != username:
            user.username = username
            await session.commit()
        return user
    user = User(telegram_id=telegram_id, username=username)
    session.add(user)
    await session.commit()
    await session.refresh(user, attribute_names=["topics"])
    return user


async def get_user_topics(session: AsyncSession, telegram_id: int) -> set[str]:
    result = await session.execute(
        select(UserTopic.topic_key)
        .join(User)
        .where(User.telegram_id == telegram_id)
    )
    return {row for (row,) in result.all()}


async def set_user_topic(
    session: AsyncSession,
    telegram_id: int,
    topic_key: str,
    enabled: bool,
    username: str | None = None,
) -> set[str]:
    user = await get_or_create_user(session, telegram_id, username)
    result = await session.execute(
        select(UserTopic).where(UserTopic.user_id == user.id, UserTopic.topic_key == topic_key)
    )
    existing = result.scalar_one_or_none()
    if enabled and not existing:
        session.add(UserTopic(user_id=user.id, topic_key=topic_key))
    elif not enabled and existing:
        await session.delete(existing)
    await session.commit()
    return await get_user_topics(session, telegram_id)


async def clear_user_topics(session: AsyncSession, telegram_id: int) -> None:
    user = await get_or_create_user(session, telegram_id)
    for topic in list(user.topics):
        await session.delete(topic)
    await session.commit()


async def get_user_sources(session: AsyncSession, telegram_id: int) -> set[str]:
    """Enabled scrape sources for a user.

    A source is enabled unless it has a row in ``user_disabled_sources``,
    so a brand-new user gets every source by default.
    """
    result = await session.execute(
        select(UserDisabledSource.source_key)
        .join(User)
        .where(User.telegram_id == telegram_id)
    )
    disabled = {row for (row,) in result.all()}
    return {key for key in ALL_SOURCE_KEYS if key not in disabled}


async def toggle_user_source(
    session: AsyncSession, telegram_id: int, source_key: str
) -> set[str]:
    """Flip a single source on/off for the user; return the new enabled set."""
    user = await get_or_create_user(session, telegram_id)
    result = await session.execute(
        select(UserDisabledSource).where(
            UserDisabledSource.user_id == user.id,
            UserDisabledSource.source_key == source_key,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        await session.delete(existing)
    else:
        session.add(UserDisabledSource(user_id=user.id, source_key=source_key))
    await session.commit()
    return await get_user_sources(session, telegram_id)


async def set_monitoring(
    session: AsyncSession,
    telegram_id: int,
    enabled: bool,
    username: str | None = None,
) -> bool:
    user = await get_or_create_user(session, telegram_id, username)
    user.monitoring_enabled = enabled
    await session.commit()
    return user.monitoring_enabled


async def is_monitoring_enabled(session: AsyncSession, telegram_id: int) -> bool:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if not user:
        return True
    return user.monitoring_enabled


async def get_active_subscribers(session: AsyncSession) -> list[User]:
    """Subscribers with monitoring enabled and their topics eagerly loaded.

    Uses selectinload so user.topics is available without a lazy trigger,
    which would raise MissingGreenlet in async context.
    """
    result = await session.execute(
        select(User)
        .options(selectinload(User.topics))
        .where(User.is_active.is_(True), User.monitoring_enabled.is_(True))
    )
    return list(result.scalars().unique().all())


async def is_post_seen(session: AsyncSession, source: str, external_id: str) -> bool:
    result = await session.execute(
        select(SeenPost.id).where(SeenPost.source == source, SeenPost.external_id == external_id)
    )
    return result.scalar_one_or_none() is not None


async def mark_post_seen(
    session: AsyncSession,
    post: JobPosting,
    notified: bool = False,
    complexity: int | None = None,
    price_value: int | None = None,
    is_vacancy: bool | None = None,
) -> SeenPost:
    if is_vacancy is None:
        is_vacancy = detect_vacancy(post)
    row = SeenPost(
        source=post.source,
        external_id=post.external_id,
        url=post.url,
        title=post.title,
        budget=post.budget,
        description=(post.description or "")[:2000],
        matched_topics=",".join(post.matched_topics) if post.matched_topics else None,
        notified=notified,
        published_at=post.published_at,
        responses=post.responses or 0,
        complexity=complexity,
        price_value=price_value,
        is_vacancy=is_vacancy,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row


async def get_top_relevant(session: AsyncSession, telegram_id: int, limit: int = 20) -> list[SeenPost]:
    """Return stored postings whose topics overlap the user's selected topics.

    Relevance is scored by the caller (per current time) so recency stays fresh.
    Job vacancies / hiring are excluded (is_vacancy = False) — the user wants
    freelance orders or long-term collaboration, not job offers.
    """
    topics = await get_user_topics(session, telegram_id)
    if not topics:
        return []
    conds = [SeenPost.matched_topics.ilike(f"%{t}%") for t in topics]
    result = await session.execute(
        select(SeenPost).where(or_(*conds), SeenPost.is_vacancy.is_(False))
    )
    return list(result.scalars().all())


async def get_recent_posts(session: AsyncSession, limit: int = 10) -> list[SeenPost]:
    """Return the most recently seen postings across all sources (raw feed).

    Ignores topic relevance — this is the literal "last N announcements" view
    the user opens to watch what just arrived from every exchange.
    """
    result = await session.execute(
        select(SeenPost).order_by(SeenPost.seen_at.desc()).limit(limit)
    )
    return list(result.scalars().all())


async def get_all_posts(session: AsyncSession, limit: int = 300) -> list[SeenPost]:
    """Return all stored postings (the full board), newest first.

    Used by the web board view. Vacancies are still shown there so the user can
    scan everything that arrived, but flagged with a badge.
    """
    result = await session.execute(
        select(SeenPost).order_by(SeenPost.seen_at.desc()).limit(limit)
    )
    return list(result.scalars().all())


async def get_relevant_posts(session: AsyncSession, limit: int = 500) -> list[SeenPost]:
    """Return non-vacancy postings for relevance ranking on the web board.

    Unlike ``get_top_relevant`` this is not tied to a Telegram user's topics —
    the public board ranks everything that isn't a vacancy. Scoring is done by
    the caller so recency stays fresh.
    """
    result = await session.execute(
        select(SeenPost)
        .where(SeenPost.is_vacancy.is_(False))
        .order_by(SeenPost.seen_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def count_stats(session: AsyncSession) -> dict:
    from sqlalchemy import func

    total = await session.scalar(select(func.count()).select_from(SeenPost)) or 0
    notified = await session.scalar(
        select(func.count()).select_from(SeenPost).where(SeenPost.notified.is_(True))
    ) or 0
    by_source_rows = await session.execute(
        select(SeenPost.source, func.count()).group_by(SeenPost.source)
    )
    by_source = {src: cnt for src, cnt in by_source_rows.all()}
    return {"total": total, "notified": notified, "by_source": by_source}


async def board_metrics(session: AsyncSession, hours: int = 24) -> dict:
    """Aggregate dashboard stats + hourly series for sparklines.

    Web board only needs the public/global view (no per-user topics or sources).
    Returns counts, average price, and a list of "new posts per hour" for the
    last ``hours`` hours (oldest first). Missing hours are zero-filled so the
    chart has a stable x-axis.
    """
    from datetime import datetime, timedelta, timezone

    now = datetime.now(timezone.utc)
    since = now - timedelta(hours=hours)

    total = await session.scalar(select(func.count()).select_from(SeenPost)) or 0
    notified = await session.scalar(
        select(func.count()).select_from(SeenPost).where(SeenPost.notified.is_(True))
    ) or 0
    vacancies = await session.scalar(
        select(func.count()).select_from(SeenPost).where(SeenPost.is_vacancy.is_(True))
    ) or 0
    fresh_24 = await session.scalar(
        select(func.count())
        .select_from(SeenPost)
        .where(SeenPost.seen_at >= since)
    ) or 0

    avg_price = await session.scalar(
        select(func.avg(SeenPost.price_value)).where(SeenPost.price_value.is_not(None))
    )
    avg_price = int(round(avg_price)) if avg_price is not None else None

    sources_enabled = await session.scalar(
        select(func.count(func.distinct(SeenPost.source)))
    ) or 0
    source_rows = await session.execute(
        select(SeenPost.source, func.count()).group_by(SeenPost.source)
    )
    by_source = {source: int(count) for source, count in source_rows.all()}

    rows = await session.execute(
        select(SeenPost.seen_at)
        .where(SeenPost.seen_at >= since)
        .order_by(SeenPost.seen_at.asc())
    )
    counts: dict[int, int] = {}
    for (ts,) in rows.all():
        if ts is None:
            continue
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        hour = int((ts - since).total_seconds() // 3600)
        if 0 <= hour < hours:
            counts[hour] = counts.get(hour, 0) + 1
    fresh_series = [counts.get(h, 0) for h in range(hours)]

    return {
        "total": int(total),
        "notified": int(notified),
        "vacancies": int(vacancies),
        "fresh_24": int(fresh_24),
        "avg_price": avg_price,
        "sources_enabled": int(sources_enabled),
        "by_source": by_source,
        "fresh_series": fresh_series,
    }


async def latest_scrape_finished_at(session: AsyncSession):
    """Return the most recent completed scrape timestamp for dashboard status."""
    return await session.scalar(select(func.max(ScrapeRun.finished_at)))
