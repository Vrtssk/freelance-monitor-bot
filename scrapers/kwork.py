import logging
import re
from urllib.parse import urljoin

from config.settings import settings
from models.schemas import JobPosting
from scrapers.base import BaseScraper, parse_relative_time, parse_responses

logger = logging.getLogger(__name__)

KWORK_URL = "https://kwork.ru/projects?c=41"
BASE = "https://kwork.ru"


class KworkScraper(BaseScraper):
    """Parse Kwork project exchange via Playwright (JS-rendered)."""

    source = "kwork"
    name = "Kwork"

    async def fetch(self) -> list[JobPosting]:
        if not settings.USE_PLAYWRIGHT:
            self._log("Playwright disabled, skip")
            return []
        try:
            html = await self._fetch_playwright(KWORK_URL)
        except Exception as exc:
            logger.exception("Kwork Playwright failed: %s", exc)
            return []
        posts = self._parse(html)
        if not posts:
            posts = await self._try_api()
        self._log(f"fetched {len(posts)} posts")
        return posts

    async def _fetch_playwright(self, url: str) -> str:
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                page = await browser.new_page(user_agent=settings.USER_AGENT)
                await page.goto(url, wait_until="networkidle", timeout=60000)
                await page.wait_for_timeout(2500)
                return await page.content()
            finally:
                await browser.close()

    def _parse(self, html: str) -> list[JobPosting]:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        posts: list[JobPosting] = []
        seen: set[str] = set()

        for a in soup.find_all("a", href=True):
            href = a["href"]
            m = re.search(r"/projects/(\d+)", href)
            if not m:
                continue
            external_id = m.group(1)
            if external_id in seen:
                continue
            title = a.get_text(strip=True)
            if not title or len(title) < 5:
                continue
            seen.add(external_id)
            url = urljoin(BASE, href)
            parent = a.find_parent(["div", "article", "li", "tr"])
            description = ""
            budget = None
            if parent:
                text = parent.get_text(" ", strip=True)
                description = re.sub(r"\s+", " ", text)[:1500]
                bm = re.search(r"(\d[\d\s]*₽|\d[\d\s]*руб)", text)
                if bm:
                    budget = bm.group(1).strip()
            full_text = f"{title} {description}"
            posts.append(
                JobPosting(
                    source=self.source,
                    external_id=external_id,
                    title=title[:300],
                    description=description,
                    budget=budget,
                    url=url,
                    published_at=parse_relative_time(full_text),
                    responses=parse_responses(full_text),
                )
            )
        return posts

    async def _try_api(self) -> list[JobPosting]:
        """Fallback: try common Kwork projects API endpoints."""
        import httpx

        candidates = [
            "https://kwork.ru/projects?c=41&page=1",
            "https://kwork.ru/projects?json=1&c=41",
        ]
        posts: list[JobPosting] = []
        async with httpx.AsyncClient(
            headers=self.headers, follow_redirects=True, timeout=30
        ) as client:
            for url in candidates:
                try:
                    resp = await client.get(url)
                    if resp.status_code != 200:
                        continue
                    ctype = resp.headers.get("content-type", "")
                    if "json" in ctype:
                        data = resp.json()
                        posts.extend(self._parse_json(data))
                        if posts:
                            break
                    else:
                        posts = self._parse(resp.text)
                        if posts:
                            break
                except Exception as exc:
                    logger.debug("Kwork API fallback %s: %s", url, exc)
        return posts

    def _parse_json(self, data) -> list[JobPosting]:
        posts: list[JobPosting] = []
        items = []
        if isinstance(data, dict):
            items = data.get("data") or data.get("projects") or data.get("wants") or []
            if isinstance(items, dict):
                items = items.get("data") or items.get("items") or []
        if not isinstance(items, list):
            return posts
        for item in items:
            if not isinstance(item, dict):
                continue
            ext = str(item.get("id") or item.get("want_id") or "")
            title = item.get("name") or item.get("title") or ""
            if not ext or not title:
                continue
            desc = item.get("description") or item.get("desc") or ""
            price = item.get("priceLimit") or item.get("price") or item.get("budget")
            budget = f"{price} ₽" if price else None
            url = item.get("url") or f"{BASE}/projects/{ext}"
            posts.append(
                JobPosting(
                    source=self.source,
                    external_id=ext,
                    title=str(title)[:300],
                    description=str(desc)[:1500],
                    budget=budget,
                    url=url if str(url).startswith("http") else urljoin(BASE, str(url)),
                )
            )
        return posts
