import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config.settings import settings
from scheduler.monitor import monitor_service

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def start_scheduler() -> None:
    if not settings.SCRAPE_ENABLED:
        logger.info("Scraping disabled (SCRAPE_ENABLED=false)")
        return
    interval = max(60, settings.SCRAPE_INTERVAL)
    scheduler.add_job(
        monitor_service.run_cycle,
        "interval",
        seconds=interval,
        id="scrape_cycle",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    if not scheduler.running:
        scheduler.start()
    logger.info("Scheduler started: every %s seconds", interval)


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
