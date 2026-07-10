import logging
from datetime import datetime, timezone

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import settings
from db.models import ScrapeRun
from db.repository import (
    get_active_subscribers,
    is_post_seen,
    mark_post_seen,
)
from db.session import async_session_factory
from filters.pipeline import HybridFilter
from models.schemas import JobPosting
from scrapers import get_all_scrapers
from utils.formatting import format_job_notification

logger = logging.getLogger(__name__)


class MonitorService:
    """Orchestrates scrape → filter → notify pipeline."""

    def __init__(self, bot: Bot | None = None) -> None:
        self.bot = bot
        self.filter = HybridFilter()
        self._running = False

    def set_bot(self, bot: Bot) -> None:
        self.bot = bot

    async def run_cycle(self) -> dict:
        if self._running:
            logger.warning("Scrape cycle already running, skip")
            return {"skipped": True}
        self._running = True
        summary = {"sources": {}, "notified": 0, "errors": []}
        try:
            scrapers = get_all_scrapers()
            all_new: list[JobPosting] = []

            async with async_session_factory() as session:
                for scraper in scrapers:
                    src_stats = await self._scrape_one(session, scraper)
                    summary["sources"][scraper.source] = src_stats
                    all_new.extend(src_stats.get("new_posts") or [])

                if not all_new:
                    logger.info("No new posts this cycle")
                    return summary

                users = await get_active_subscribers(session)
                if not users:
                    logger.info("No active subscribers")
                    for post in all_new:
                        if not await is_post_seen(session, post.source, post.external_id):
                            await mark_post_seen(session, post, notified=False)
                    return summary

                # Union of all user topics for filtering efficiency
                for user in users:
                    user_topics = {t.topic_key for t in user.topics}
                    if not user_topics:
                        continue
                    matched = await self.filter.filter_posts(all_new, user_topics)
                    for post in matched:
                        already = await is_post_seen(session, post.source, post.external_id)
                        if already:
                            continue
                        sent = await self._notify_user(user.telegram_id, post)
                        await mark_post_seen(session, post, notified=sent)
                        if sent:
                            summary["notified"] += 1

                # Mark remaining new posts as seen (no match)
                for post in all_new:
                    if not await is_post_seen(session, post.source, post.external_id):
                        await mark_post_seen(session, post, notified=False)

            return summary
        except Exception as exc:
            logger.exception("Monitor cycle failed: %s", exc)
            summary["errors"].append(str(exc))
            return summary
        finally:
            self._running = False

    async def _scrape_one(self, session: AsyncSession, scraper) -> dict:
        run = ScrapeRun(source=scraper.source)
        session.add(run)
        await session.commit()
        stats = {"found": 0, "new": 0, "new_posts": [], "error": None}
        try:
            posts = await scraper.fetch()
            stats["found"] = len(posts)
            new_posts: list[JobPosting] = []
            for post in posts:
                if await is_post_seen(session, post.source, post.external_id):
                    continue
                new_posts.append(post)
            stats["new"] = len(new_posts)
            stats["new_posts"] = new_posts
            run.posts_found = stats["found"]
            run.posts_new = stats["new"]
            run.finished_at = datetime.now(timezone.utc)
            await session.commit()
        except Exception as exc:
            logger.exception("Scraper %s failed: %s", scraper.source, exc)
            stats["error"] = str(exc)
            run.error = str(exc)[:2000]
            run.finished_at = datetime.now(timezone.utc)
            await session.commit()
        return stats

    async def _notify_user(self, telegram_id: int, post: JobPosting) -> bool:
        if not self.bot:
            logger.warning("No bot instance, cannot notify")
            return False
        try:
            text = format_job_notification(post)
            await self.bot.send_message(telegram_id, text, disable_web_page_preview=False)
            return True
        except Exception as exc:
            logger.warning("Notify %s failed: %s", telegram_id, exc)
            return False


monitor_service = MonitorService()
