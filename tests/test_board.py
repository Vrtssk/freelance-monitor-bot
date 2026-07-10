from db.models import SeenPost

from api.board import render_jobs_page


def _row(**kw) -> SeenPost:
    base = dict(
        source="fl_ru",
        external_id="1",
        title="Тестовое объявление",
        budget="10 000 ₽",
        url="https://fl.ru/projects/1",
        matched_topics="chatbots",
        description="Описание поста для доски.",
        is_vacancy=False,
        notified=True,
    )
    base.update(kw)
    return SeenPost(**base)


def test_render_contains_title_and_link():
    html = render_jobs_page([_row()])
    assert "<!DOCTYPE html>" in html
    assert "Тестовое объявление" in html
    assert "https://fl.ru/projects/1" in html
    assert "💰 10 000 ₽" in html
    assert "прислано" in html  # notified badge


def test_render_vacancy_badge():
    html = render_jobs_page([_row(is_vacancy=True, notified=False)])
    assert "вакансия" in html


def test_render_empty():
    html = render_jobs_page([])
    assert "Пока нет" in html


def test_render_has_source_filter():
    html = render_jobs_page([_row(source="kwork", external_id="2", title="Kwork пост")])
    assert "kwork" in html  # data-src used by JS filter
