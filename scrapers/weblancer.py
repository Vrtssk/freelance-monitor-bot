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
                await page.goto(url, wait_until="networkidle", timeout=60000)
                await page.wait_for_timeout(2000)
                return await page.content()
            finally:
                await browser.close()

    def _parse(self, html: str) -> list[JobPosting]:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        posts: list[JobPosting] = []
        seen_ids: set[str] = set()

        for a in soup.find_all("a", href=True):
            href = a["href"]
            m = re.search(r"/freelance/([a-z0-9-]+)-(\d+)/?", href)
            if not m:
                continue
            slug, external_id = m.group(1), m.group(2)
            # category pages end with short ids like -31; job pages have larger ids
            if len(external_id) < 5:
                continue
            if external_id in seen_ids:
                continue
            title = a.get_text(strip=True)
            if not title or len(title) < 8:
                continue
            # skip nav/tag chips
            if len(title) > 200:
                title = title[:200]
            seen_ids.add(external_id)
            url = urljoin(BASE, href)
            parent = a.find_parent(["article", "div", "li", "section"])
            description = ""
            budget = None
            if parent:
                text = parent.get_text(" ", strip=True)
                description = re.sub(r"\s+", " ", text)[:1500]
                bm = re.search(r"(\d[\d\s]*[₽$]|договорн\w*|обсужда\w*)", text, re.I)
                if bm:
                    budget = bm.group(1).strip()
            full_text = f"{title} {description}"
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
