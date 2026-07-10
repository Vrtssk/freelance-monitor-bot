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
