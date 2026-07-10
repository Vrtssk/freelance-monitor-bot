from abc import ABC, abstractmethod
import logging
import re
from datetime import datetime, timedelta, timezone

import httpx

from config.settings import settings
from models.schemas import JobPosting

logger = logging.getLogger(__name__)

# Russian relative-time phrases -> published_at.
_RESP_RE = re.compile(r"(\d+)\s*(?:предложени\w*|отклик\w*|заяв\w*)", re.I)


def parse_relative_time(text: str | None) -> datetime | None:
    """Best-effort parse of Russian relative publish time into a datetime (UTC)."""
    if not text:
        return None
    now = datetime.now(timezone.utc)
    low = text.lower()
    if "только что" in low or "сегодня" in low:
        return now
    if "вчера" in low:
        return now - timedelta(days=1)
    m = re.search(r"(\d+)\s*(?:минут[а-я]*|мин\b)", low)
    if m:
        return now - timedelta(minutes=int(m.group(1)))
    m = re.search(r"(\d+)\s*(?:час[а-я]*|ч\b)", low)
    if m:
        return now - timedelta(hours=int(m.group(1)))
    m = re.search(r"(\d+)\s*(?:дн[яей]?|день)", low)
    if m:
        return now - timedelta(days=int(m.group(1)))
    m = re.search(r"(\d+)\s*недел", low)
    if m:
        return now - timedelta(weeks=int(m.group(1)))
    m = re.search(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", low)
    if m:
        try:
            return datetime(
                int(m.group(3)), int(m.group(2)), int(m.group(1)), tzinfo=timezone.utc
            )
        except ValueError:
            pass
    m = re.search(r"(\d{1,2})\.(\d{1,2})", low)
    if m:
        try:
            return datetime(
                now.year, int(m.group(2)), int(m.group(1)), tzinfo=timezone.utc
            )
        except ValueError:
            pass
    return None


def parse_responses(text: str | None) -> int:
    """Best-effort parse of the number of responses/offers from listing text."""
    if not text:
        return 0
    m = _RESP_RE.search(text)
    return int(m.group(1)) if m else 0


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
