import logging
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from models.schemas import JobPosting
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

# c[]=4 — Веб-разработка и IT
FREELANCE_URL = "https://freelance.ru/task?c%5B%5D=4&a=1"
BASE = "https://freelance.ru"


class FreelanceRuScraper(BaseScraper):
    """Parse Freelance.ru task cards (Веб-разработка и IT)."""

    source = "freelance_ru"
    name = "Freelance.ru"

    async def fetch(self) -> list[JobPosting]:
        html = await self._get_html(FREELANCE_URL)
        posts = self._parse(html)
        self._log(f"fetched {len(posts)} posts")
        return posts

    def _parse(self, html: str) -> list[JobPosting]:
        soup = BeautifulSoup(html, "html.parser")
        posts: list[JobPosting] = []
        for card in soup.select("article.task-card"):
            try:
                post = self._parse_card(card)
                if post:
                    posts.append(post)
            except Exception as exc:
                logger.warning("Freelance.ru card parse error: %s", exc)
        return posts

    def _parse_card(self, card) -> JobPosting | None:
        title_a = card.select_one("a.task-card__title-link")
        if not title_a:
            return None
        title = title_a.get_text(strip=True)
        href = title_a.get("href") or ""
        url = urljoin(BASE, href)

        m = re.search(r"/task/view/(\d+)", href)
        if not m:
            m = re.search(r"/(\d+)/?$", href)
        if not m:
            return None
        external_id = m.group(1)

        desc_el = card.select_one("p.task-card__desc")
        description = ""
        if desc_el:
            description = desc_el.get_text(" ", strip=True)
            description = re.sub(r"\s+", " ", description)[:1500]

        budget_el = card.select_one(".task-card__budget")
        budget = None
        if budget_el:
            budget = budget_el.get_text(" ", strip=True)
            budget = re.sub(r"\s+", " ", budget).strip()
            if "обсуждается" in budget.lower() or "индивидуально" in budget.lower():
                budget = "Обсуждается"

        cat_el = card.select_one(".task-chip--cat, .task-chip.task-chip--cat")
        category = cat_el.get_text(strip=True) if cat_el else None

        return JobPosting(
            source=self.source,
            external_id=external_id,
            title=title,
            description=description,
            budget=budget,
            url=url,
            category=category,
        )
