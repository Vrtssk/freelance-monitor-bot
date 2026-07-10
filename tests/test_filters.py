from models.schemas import JobPosting

from filters.keywords import match_keywords
from filters.vacancy import is_vacancy


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


# --- vacancy detection -----------------------------------------------------


def test_vacancy_interview_example_is_detected():
    # Real FL.ru "Срочный заказ" that is actually a job hire ("по результатам
    # собеседования"). Must be classified as a vacancy, not a freelance order.
    post = _post(
        "программист",
        "Срочный заказ. Оплата: по результатам собеседования. "
        "Требуется программист с опытом работы и знаниями.",
    )
    assert is_vacancy(post) is True


def test_vacancy_full_time_is_detected():
    post = _post(
        "Требуется Python-разработчик",
        "Полная занятость, офис. Оклад по результатам собеседования.",
    )
    assert is_vacancy(post) is True


def test_freelance_order_is_not_vacancy():
    # The user's example of a relevant one-off order (freelance.ru).
    post = _post(
        "Разработчик/AI-специалист для быстрой генерации HTML/Next.js сайтов",
        "Ищем человека, который умеет с помощью ИИ быстро генерировать код "
        "простых сайтов. Гонорар обсуждается индивидуально. Разовое. Срок 3 дня.",
    )
    assert is_vacancy(post) is False


def test_ordinary_freelance_task_is_not_vacancy():
    post = _post(
        "Адаптивная вёрстка лендинга по Figma-макету",
        "Требуется сверстать одностраничный лендинг. Бюджет обсуждаем.",
    )
    assert is_vacancy(post) is False
