import json
import logging
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from models.schemas import JobPosting
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

FL_URL = "https://www.fl.ru/projects/category/programmirovanie/"
BASE = "https://www.fl.ru"


class FlRuScraper(BaseScraper):
    """Parse FL.ru programming projects from HTML + JSON-LD ItemList."""

    source = "fl_ru"
    name = "FL.ru"

    async def fetch(self) -> list[JobPosting]:
        html = await self._get_html(FL_URL)
        posts = self._parse_html(html)
        if not posts:
            posts = self._parse_json_ld(html)
        self._log(f"fetched {len(posts)} posts")
        return posts

    def _parse_html(self, html: str) -> list[JobPosting]:
        soup = BeautifulSoup(html, "html.parser")
        posts: list[JobPosting] = []
        for block in soup.select("div.b-post[id^=project-item]"):
            try:
                post = self._parse_block(block)
                if post:
                    posts.append(post)
            except Exception as exc:
                logger.warning("FL.ru block parse error: %s", exc)
        return posts

    def _parse_block(self, block) -> JobPosting | None:
        block_id = block.get("id") or ""
        m = re.search(r"project-item(\d+)", block_id)
        if not m:
            return None
        external_id = m.group(1)

        title_a = block.select_one("h2.b-post__title a, a[id^=prj_name_]")
        if not title_a:
            return None
        title = title_a.get_text(strip=True)
        href = title_a.get("href") or ""
        url = urljoin(BASE, href)

        price_el = block.select_one(".b-post__price")
        budget = price_el.get_text(" ", strip=True) if price_el else None
        if budget:
            budget = re.sub(r"\s+", " ", budget).strip()

        desc_el = block.select_one(".b-post__txt, .b-post__body .b-post__txt")
        description = desc_el.get_text(" ", strip=True) if desc_el else ""
        if description:
            description = re.sub(r"\s+", " ", description)[:1500]

        return JobPosting(
            source=self.source,
            external_id=external_id,
            title=title,
            description=description,
            budget=budget or None,
            url=url,
        )

    def _parse_json_ld(self, html: str) -> list[JobPosting]:
        soup = BeautifulSoup(html, "html.parser")
        posts: list[JobPosting] = []
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "")
            except (json.JSONDecodeError, TypeError):
                continue
            graph = data.get("@graph") if isinstance(data, dict) else None
            items = None
            if graph:
                for node in graph:
                    if isinstance(node, dict) and node.get("@type") == "ItemList":
                        items = node.get("itemListElement") or []
                        break
            elif isinstance(data, dict) and data.get("@type") == "ItemList":
                items = data.get("itemListElement") or []
            if not items:
                continue
            for item in items:
                if not isinstance(item, dict):
                    continue
                url = item.get("url") or ""
                name = item.get("name") or ""
                m = re.search(r"/projects/(\d+)/", url)
                if not m or not name:
                    continue
                posts.append(
                    JobPosting(
                        source=self.source,
                        external_id=m.group(1),
                        title=name,
                        description="",
                        url=url,
                    )
                )
        return posts
