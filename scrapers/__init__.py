from scrapers.base import BaseScraper
from scrapers.fl_ru import FlRuScraper
from scrapers.freelance_ru import FreelanceRuScraper
from scrapers.kwork import KworkScraper
from scrapers.weblancer import WeblancerScraper


def get_all_scrapers() -> list[BaseScraper]:
    return [
        FlRuScraper(),
        FreelanceRuScraper(),
        WeblancerScraper(),
        KworkScraper(),
    ]
