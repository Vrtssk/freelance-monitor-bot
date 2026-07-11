from scrapers.base import BaseScraper
from scrapers.fl_ru import FlRuScraper
from scrapers.freelance_ru import FreelanceRuScraper
from scrapers.kwork import KworkScraper
from scrapers.weblancer import WeblancerScraper

from config.sources import ALL_SOURCE_KEYS

_SCRAPERS = {
    "fl_ru": FlRuScraper,
    "freelance_ru": FreelanceRuScraper,
    "weblancer": WeblancerScraper,
    "kwork": KworkScraper,
}


def get_all_scrapers() -> list[BaseScraper]:
    """All scrapers, in canonical source order."""
    return [_SCRAPERS[key]() for key in ALL_SOURCE_KEYS]


def get_scrapers(enabled: set[str] | None = None) -> list[BaseScraper]:
    """Scrapers limited to the given enabled source keys (canonical order).

    ``enabled=None`` returns every scraper (used by ad-hoc tests / main run when
    no per-user filtering is required).
    """
    if enabled is None:
        return get_all_scrapers()
    return [_SCRAPERS[key]() for key in ALL_SOURCE_KEYS if key in enabled]
