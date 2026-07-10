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


def test_weblancer_parse():
    from scrapers.weblancer import WeblancerScraper

    html = _load("weblancer.html")
    posts = WeblancerScraper()._parse(html)
    assert posts, "Weblancer parser returned no posts"
    post = posts[0]
    assert post.source == "weblancer"
    # Job id must be the long trailing id, not the short category id (-31).
    assert post.external_id.isdigit() and len(post.external_id) >= 5
    assert post.url.startswith("https://www.weblancer.net/freelance/")
    assert post.title
    # At least one post should carry a parsed responses count and publish date.
    assert any(p.responses for p in posts), "no responses parsed"
    assert any(p.published_at for p in posts), "no publish dates parsed"
