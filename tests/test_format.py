from models.schemas import JobPosting

from utils.formatting import format_job_notification


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
