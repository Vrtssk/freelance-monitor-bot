from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import SeenPost, User, UserTopic
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
) -> SeenPost:
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
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row


async def get_top_relevant(session: AsyncSession, telegram_id: int, limit: int = 20) -> list[SeenPost]:
    """Return stored postings whose topics overlap the user's selected topics.

    Relevance is scored by the caller (per current time) so recency stays fresh.
    """
    topics = await get_user_topics(session, telegram_id)
    if not topics:
        return []
    conds = [SeenPost.matched_topics.ilike(f"%{t}%") for t in topics]
    result = await session.execute(select(SeenPost).where(or_(*conds)))
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
