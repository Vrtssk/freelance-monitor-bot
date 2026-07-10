from abc import ABC, abstractmethod
import logging

import httpx

from config.settings import settings
from models.schemas import JobPosting

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Base scraper: fetch listing page(s) and return normalized JobPosting list."""

    source: str = "unknown"
    name: str = "Unknown"

    def __init__(self) -> None:
        self.headers = {
            "User-Agent": settings.USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        }

    @abstractmethod
    async def fetch(self) -> list[JobPosting]:
        """Fetch and parse current job listings."""

    async def _get_html(self, url: str, timeout: float = 30.0) -> str:
        async with httpx.AsyncClient(
            headers=self.headers,
            follow_redirects=True,
            timeout=timeout,
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.text

    def _log(self, msg: str) -> None:
        logger.info("[%s] %s", self.source, msg)
