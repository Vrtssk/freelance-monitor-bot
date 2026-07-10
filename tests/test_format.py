from models.schemas import JobPosting

from db.models import SeenPost
from utils.formatting import format_job_notification, format_recent_list, format_top_list


def test_format_real_post_contains_fields():
    post = JobPosting(
        source="fl_ru",
        external_id="123",
        title="Разработка Telegram-бота на aiogram",
        description="Нужен бот для магазина. Интеграция с CRM.",
        budget="35 000 ₽",
        url="https://fl.ru/projects/123/",
        matched_topics=["chatbots"],
    )
    text = format_job_notification(post)
    assert "Разработка Telegram-бота" in text
    assert "35 000 ₽" in text
    assert "chatbots" not in text  # emoji label used, not raw key
    assert "🤖" in text
    assert "https://fl.ru/projects/123/" in text
    assert "FL.ru" in text


def test_format_escapes_html():
    post = JobPosting(
        source="fl_ru",
        external_id="9",
        title="<b>Опасный</b> заголовок & 'кавычки'",
        description="",
        url="https://fl.ru/projects/9/",
        matched_topics=["scripts"],
    )
    text = format_job_notification(post)
    assert "Опасный" in text
    assert "&lt;b&gt;Опасный&lt;/b&gt;" in text
    assert "&amp;" in text


def test_format_no_debug_reason_leaks():
    """Internal match reasons (e.g. 'keywords (llm unavailable)') must not show."""
    post = JobPosting(
        source="fl_ru",
        external_id="1",
        title="Парсинг каталога (Scrapy)",
        description="Нужен парсер.",
        url="https://fl.ru/projects/1/",
        matched_topics=["parsing"],
        match_reason="keywords (llm unavailable)",
    )
    text = format_job_notification(post)
    assert "llm unavailable" not in text
    assert "keywords" not in text


def test_format_strips_kwork_artifacts_and_duplicate_title():
    """Kwork descriptions embed the title and a 'Показать полностью' button."""
    post = JobPosting(
        source="kwork",
        external_id="3214057",
        title="Бот для мониторинга чатов",
        description=(
            "Бот для мониторинга чатов… Показать полностью Нужно разработать "
            "простой бот для поиска лидов."
        ),
        budget="10 000 ₽",
        url="https://kwork.ru/projects/3214057",
        matched_topics=["chatbots"],
    )
    text = format_job_notification(post)
    assert "Показать полностью" not in text
    # title must appear once (as the header), not duplicated in the description
    assert text.count("Бот для мониторинга чатов") == 1
    assert "Нужно разработать" in text
    assert "🤖 Чат-боты" in text


def test_format_truncates_long_description():
    post = JobPosting(
        source="fl_ru",
        external_id="2",
        title="Длинное описание",
        description="Слово " * 400,
        url="https://fl.ru/projects/2/",
        matched_topics=["scripts"],
    )
    text = format_job_notification(post)
    # description block is the paragraph before the trailing link
    desc_block = text.split("\n\n")[-2]
    assert desc_block.endswith("…")
    # description block should not exceed ~DESC_MAX by a wide margin
    assert len(desc_block) < 800


def test_format_missing_budget_shows_default():
    post = JobPosting(
        source="fl_ru",
        external_id="3",
        title="Без бюджета",
        description="",
        url="https://fl.ru/projects/3/",
        matched_topics=["frontend"],
    )
    text = format_job_notification(post)
    assert "Не указан" in text


def test_format_dedupes_repeated_kwork_description():
    """Kwork embeds a truncated preview followed by the full text; keep one copy."""
    body = (
        "Нужно создать Telegram-бота для заявок. Что должен уметь: -"
        " принимать обращения; - собирать имя и телефон"
    )
    repeated = body[:30] + "... " + body
    post = JobPosting(
        source="kwork",
        external_id="3214327",
        title="AI-менеджер в Telegram для заявок",
        description=repeated,
        url="https://kwork.ru/projects/3214327",
        matched_topics=["chatbots"],
    )
    text = format_job_notification(post)
    # the leading phrase must not appear twice
    assert text.count("Нужно создать Telegram-бота") == 1
    assert "🔗" in text


def test_format_link_is_html_anchor():
    post = JobPosting(
        source="kwork",
        external_id="3214327",
        title="Заголовок",
        description="Описание поста.",
        url="https://kwork.ru/projects/3214327",
        matched_topics=["chatbots"],
    )
    text = format_job_notification(post)
    assert '<a href="https://kwork.ru/projects/3214327">Kwork</a>' in text


def test_format_top_list_renders():
    row = SeenPost(
        source="kwork",
        external_id="1",
        title="Тестовое объявление",
        budget="10 000 ₽",
        url="https://kwork.ru/projects/1",
        matched_topics="chatbots",
        responses=0,
        complexity=3,
        price_value=10000,
    )
    text = format_top_list([(row, 0.82)])
    assert "Топ-5" in text
    assert "82%" in text
    assert "🔗" in text
    assert "kwork.ru/projects/1" in text


def test_format_top_list_empty():
    assert "Пока нет" in format_top_list([])


def test_format_recent_list_renders():
    rows = [
        SeenPost(
            source="kwork",
            external_id="1",
            title="Последнее объявление",
            budget="10 000 ₽",
            url="https://kwork.ru/projects/1",
            matched_topics="chatbots",
        ),
        SeenPost(
            source="fl_ru",
            external_id="2",
            title="Ещё одно",
            budget=None,
            url="https://fl.ru/projects/2",
            matched_topics=None,
        ),
    ]
    text = format_recent_list(rows)
    assert "Последние 10" in text
    assert "1." in text and "2." in text
    assert "Последнее объявление" in text
    assert "Ещё одно" in text
    assert "Не указан" in text
    assert "kwork.ru/projects/1" in text


def test_format_recent_list_empty():
    assert "Пока нет" in format_recent_list([])
