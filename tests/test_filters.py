from models.schemas import JobPosting

from filters.keywords import match_keywords


def _post(title: str, description: str = "", category: str = "") -> JobPosting:
    return JobPosting(
        source="fl_ru",
        external_id="1",
        title=title,
        description=description,
        url="https://example.com/1",
        category=category,
    )


def test_keyword_match_frontend():
    post = _post("Разработка SPA на React и TypeScript")
    matched = match_keywords(post)
    assert "frontend" in matched


def test_keyword_match_markup():
    post = _post("Адаптивная вёрстка лендинга по Figma")
    assert "markup" in match_keywords(post)


def test_keyword_match_parsing():
    post = _post("Нужен парсинг каталога с маркетплейса")
    assert "parsing" in match_keywords(post)


def test_keyword_match_chatbots():
    post = _post("Telegram-бот на aiogram для магазина")
    assert "chatbots" in match_keywords(post)


def test_keyword_no_match_for_unrelated():
    post = _post("Перевод текстов с английского на русский")
    assert match_keywords(post) == []


def test_keyword_filter_by_topic_subset():
    post = _post("Разработка SPA на React и TypeScript")
    assert match_keywords(post, {"markup", "parsing"}) == []
    assert "frontend" in match_keywords(post, {"frontend", "chatbots"})
