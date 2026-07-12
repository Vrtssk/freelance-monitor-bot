import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from datetime import datetime, timezone

from config.settings import settings
from api.board import render_grid_partial, render_jobs_page, render_top_page
from db.repository import board_metrics, count_stats, get_all_posts, get_relevant_posts
from db.session import async_session_factory, init_db
from scrapers import get_all_scrapers
from scheduler.monitor import monitor_service
from utils.relevance import age_hours_from, compute_relevance

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    logger.info("API started, DB initialized")
    yield


app = FastAPI(
    title="Freelance Monitor API",
    description="Backend for Telegram freelance monitor bot",
    version="1.0.0",
    lifespan=lifespan,
)


class HealthResponse(BaseModel):
    status: str
    scrape_enabled: bool
    llm_enabled: bool


class ScrapeTriggerResponse(BaseModel):
    ok: bool
    summary: dict


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="ok",
        scrape_enabled=settings.SCRAPE_ENABLED,
        llm_enabled=settings.LLM_ENABLED and bool(settings.LLM_API_KEY),
    )


@app.get("/", response_class=HTMLResponse)
async def board(request: Request, partial: bool = False, src: str = None):
    """Web board: all collected postings, newest first.

    ``?partial=1`` returns only the card grid (for HTMX swaps); ``src`` filters
    by exchange without a full page reload.
    """
    async with async_session_factory() as session:
        rows = await get_all_posts(session)
        metrics = await board_metrics(session)
    if partial:
        return HTMLResponse(
            render_grid_partial(rows, src=src, empty_text="Пока нет сохранённых объявлений.")
        )
    return HTMLResponse(render_jobs_page(rows, metrics=metrics, base_url=str(request.base_url)))


@app.get("/top", response_class=HTMLResponse)
async def board_top(request: Request, limit: int = 10, partial: bool = False, src: str = None):
    """Web board: top-N most relevant (non-vacancy) postings."""
    async with async_session_factory() as session:
        rows = await get_relevant_posts(session)
        metrics = await board_metrics(session)
    now = datetime.now(timezone.utc)
    scored = [
        (
            row,
            compute_relevance(
                responses=row.responses or 0,
                age_hours=age_hours_from(now, row.published_at, row.seen_at),
                complexity=row.complexity or 3,
                price=row.price_value,
            ),
        )
        for row in rows
    ]
    scored.sort(key=lambda x: x[1], reverse=True)
    scored = scored[:limit]
    if partial:
        rows_top = [row for row, _ in scored]
        scores = {row.id: score for row, score in scored}
        return HTMLResponse(
            render_grid_partial(rows_top, src=src, scores=scores, empty_text="Пока нет подходящих объявлений.")
        )
    return HTMLResponse(render_top_page(scored, metrics=metrics, base_url=str(request.base_url)))


@app.get("/stats")
async def stats():
    async with async_session_factory() as session:
        return await count_stats(session)


@app.post("/scrape/run", response_model=ScrapeTriggerResponse)
async def scrape_run():
    """Manually trigger one scrape cycle (admin/debug)."""
    summary = await monitor_service.run_cycle()
    # strip non-serializable posts from response
    clean = {
        "notified": summary.get("notified", 0),
        "errors": summary.get("errors", []),
        "sources": {},
    }
    for src, st in (summary.get("sources") or {}).items():
        clean["sources"][src] = {
            "found": st.get("found", 0),
            "new": st.get("new", 0),
            "error": st.get("error"),
        }
    return ScrapeTriggerResponse(ok=True, summary=clean)


@app.get("/scrapers")
async def list_scrapers():
    return [
        {"source": s.source, "name": s.name}
        for s in get_all_scrapers()
    ]


@app.post("/scrapers/{source}/test")
async def test_scraper(source: str):
    """Fetch one source and return sample posts (no DB write)."""
    scrapers = {s.source: s for s in get_all_scrapers()}
    scraper = scrapers.get(source)
    if not scraper:
        raise HTTPException(404, f"Unknown source: {source}")
    try:
        posts = await scraper.fetch()
    except Exception as exc:
        raise HTTPException(500, str(exc)) from exc
    return {
        "source": source,
        "count": len(posts),
        "posts": [p.model_dump(mode="json") for p in posts[:10]],
    }
