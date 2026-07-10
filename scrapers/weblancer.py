import logging
import re
from urllib.parse import urljoin

from config.settings import settings
from models.schemas import JobPosting
from scrapers.base import BaseScraper, parse_relative_time, parse_responses

logger = logging.getLogger(__name__)

WEBLANCER_URL = "https://www.weblancer.net/freelance/veb-programmirovanie-31/"
BASE = "https://www.weblancer.net"


class WeblancerScraper(BaseScraper):
    """Parse Weblancer Next.js job list via Playwright (JS-rendered)."""

    source = "weblancer"
    name = "Weblancer"

    async def fetch(self) -> list[JobPosting]:
        if not settings.USE_PLAYWRIGHT:
            self._log("Playwright disabled, skip")
            return []
        try:
            html = await self._fetch_playwright(WEBLANCER_URL)
        except Exception as exc:
            logger.exception("Weblancer Playwright failed: %s", exc)
            return []
        posts = self._parse(html)
        self._log(f"fetched {len(posts)} posts")
        return posts

    async def _fetch_playwright(self, url: str) -> str:
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                page = await browser.new_page(user_agent=settings.USER_AGENT)
                # `networkidle` is unreliable here (analytics/long-poll keep the
                # network busy). Load the DOM, then wait for the job cards.
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                try:
                    await page.wait_for_selector("article.bg-white", timeout=20000)
                except Exception:
                    await page.wait_for_timeout(3000)
                return await page.content()
            finally:
                await browser.close()

    # Job URLs look like /freelance/<category-slug>/<job-slug>-<id>/ where the
    # job id has 5+ digits (category ids like -31 are short and must be ignored).
    _JOB_RE = re.compile(r"/freelance/[a-z0-9-]+/[a-z0-9-]+-(\d{5,})/?$")
    _PRICE_RE = re.compile(r"\d[\d\s]*\s*(?:₽|\$)|договорн\w*", re.I)

    def _parse(self, html: str) -> list[JobPosting]:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        posts: list[JobPosting] = []
        seen_ids: set[str] = set()

        for a in soup.find_all("a", href=True):
            href = a["href"]
            m = self._JOB_RE.search(href)
            if not m:
                continue
            external_id = m.group(1)
            if external_id in seen_ids:
                continue
            title = a.get_text(strip=True)
            if not title or len(title) < 5:
                continue
            seen_ids.add(external_id)
            title = title[:200]
            url = urljoin(BASE, href)

            # Nearest card container is an <article>/<div> with class "bg-white".
            card = a.find_parent(
                lambda tag: "bg-white" in (tag.get("class") or [])
            )
            description = ""
            budget = None
            card_text = ""
            if card:
                card_text = re.sub(r"\s+", " ", card.get_text(" ", strip=True))
                description = card_text[:1500]
                pm = self._PRICE_RE.search(card_text)
                if pm:
                    budget = re.sub(r"\s+", " ", pm.group(0)).strip()

            full_text = card_text or title
            posts.append(
                JobPosting(
                    source=self.source,
                    external_id=external_id,
                    title=title,
                    description=description,
                    budget=budget,
                    url=url,
                    published_at=parse_relative_time(full_text),
                    responses=parse_responses(full_text),
                )
            )
        return posts
