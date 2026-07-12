from db.models import SeenPost

from api.board import render_jobs_page, render_top_page


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
    assert "10 000 ₽" in html
    assert "Отправлено" in html  # notified badge


def test_render_vacancy_badge():
    html = render_jobs_page([_row(is_vacancy=True, notified=False)])
    assert "Вакансия" in html


def test_render_empty():
    html = render_jobs_page([])
    assert "Пока нет" in html


def test_render_has_source_filter():
    html = render_jobs_page([_row(source="kwork", external_id="2", title="Kwork пост")])
    assert "kwork" in html  # data-src used by JS filter


def test_render_has_nav_links():
    html = render_jobs_page([_row()])
    assert 'href="/"' in html
    assert 'href="/top"' in html
    assert "Топ заказов" in html


def test_render_top_page_shows_score_badge():
    html = render_top_page([(_row(), 0.87)])
    assert "87%" in html
    assert "score-wrap" in html
    assert "Тестовое объявление" in html
    # nav marks the top page active
    assert 'side-link active' in html


def test_render_top_page_empty():
    html = render_top_page([])
    assert "Пока нет подходящих" in html
