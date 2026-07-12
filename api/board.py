"""Server-rendered HTML board of collected job postings.

Pages are rendered with Jinja2 templates (тёмный дашборд из ``docs/site-design.md``).
HTMX swaps the card grid in place and polls for fresh posts; Alpine.js holds
the active-source filter state locally. The same ``partials/grid.html`` is
used for the full page and for HTMX partial responses (``?partial=1``).
"""
from typing import Optional

from fastapi.templating import Jinja2Templates

from config.topics import SOURCES, TOPIC_BY_KEY

templates = Jinja2Templates(directory="templates")

_TOPICS_MAP = {
    key: f"{t['emoji']} {t['name']}" for key, t in TOPIC_BY_KEY.items()
}

# Цвета источников и тем задаются здесь, чтобы шаблоны оставались чистыми.
_SOURCE_COLORS = {
    "fl_ru": "#2f81f7",
    "freelance_ru": "#00e676",
    "weblancer": "#1f9d9d",
    "kwork": "#ff9800",
}

_TOPIC_COLORS = {
    "frontend":    "#2f81f7",
    "markup":      "#ff9800",
    "parsing":     "#8957e5",
    "automation":  "#1f9d9d",
    "chatbots":    "#00e676",
}

_EMPTY_METRICS = {
    "total": 0,
    "notified": 0,
    "vacancies": 0,
    "fresh_24": 0,
    "avg_price": None,
    "sources_enabled": 0,
    "by_source": {},
    "fresh_series": [],
}


def _filter_by_source(rows, src: Optional[str]) -> list:
    if not src or src == "all":
        return rows
    return [r for r in rows if r.source == src]


def render_jobs_page(rows: list, metrics: Optional[dict] = None, base_url: str = "") -> str:
    """`GET /` — все объявления + метрики для дашборда."""
    return templates.get_template("board.html").render(
        active="all",
        rows=rows,
        sources=SOURCES,
        source_colors=_SOURCE_COLORS,
        topic_colors=_TOPIC_COLORS,
        topics_map=_TOPICS_MAP,
        metrics=metrics or _EMPTY_METRICS,
    )


def render_top_page(scored: list, metrics: Optional[dict] = None, base_url: str = "") -> str:
    """`GET /top` — топ-N самых релевантных объявлений.

    ``scored`` is a list of ``(row, score)`` tuples. The tests may pass bare rows
    (no score), so we tolerate both shapes.
    """
    items: list[tuple] = []
    for item in scored:
        if isinstance(item, tuple):
            row, score = item
        else:
            row, score = item, 0.0
        items.append((row, score))
    rows = [row for row, _ in items]
    scores = {row.id: score for row, score in items}
    return templates.get_template("top.html").render(
        active="top",
        rows=rows,
        scores=scores,
        sources=SOURCES,
        source_colors=_SOURCE_COLORS,
        topic_colors=_TOPIC_COLORS,
        topics_map=_TOPICS_MAP,
        metrics=metrics or _EMPTY_METRICS,
        empty_text="Пока нет подходящих объявлений.",
    )


def render_grid_partial(
    rows: list,
    src: Optional[str] = None,
    scores: Optional[dict] = None,
    empty_text: Optional[str] = None,
) -> str:
    """HTMX fragment: just the card grid (optionally filtered by source)."""
    if src and src != "all" and src != "top":
        rows = _filter_by_source(rows, src)
    return templates.get_template("partials/grid.html").render(
        rows=rows,
        scores=scores,
        sources=SOURCES,
        source_colors=_SOURCE_COLORS,
        topic_colors=_TOPIC_COLORS,
        topics_map=_TOPICS_MAP,
        empty_text=empty_text,
    )
