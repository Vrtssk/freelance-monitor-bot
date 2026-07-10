from pathlib import Path

from filters.keywords import match_keywords
from models.schemas import JobPosting

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_fl_ru_html_parse():
    from scrapers.fl_ru import FlRuScraper

    html = _load("fl_ru.html")
    posts = FlRuScraper()._parse_html(html)
    assert posts, "FL.ru HTML parser returned no posts"
    post = posts[0]
    assert post.source == "fl_ru"
    assert post.external_id.isdigit()
    assert post.url.startswith("https://www.fl.ru/projects/")
    assert post.title


def test_fl_ru_json_ld_parse():
    from scrapers.fl_ru import FlRuScraper

    html = _load("fl_ru.html")
    posts = FlRuScraper()._parse_json_ld(html)
    assert posts, "FL.ru JSON-LD parser returned no posts"
    for p in posts:
        assert p.external_id.isdigit()
        assert p.title


def test_freelance_ru_parse():
    from scrapers.freelance_ru import FreelanceRuScraper

    html = _load("freelance_ru.html")
    posts = FreelanceRuScraper()._parse(html)
    assert posts, "Freelance.ru parser returned no posts"
    post = posts[0]
    assert post.source == "freelance_ru"
    assert post.url.startswith("https://freelance.ru/task/view/")
    assert post.title
    assert post.description
