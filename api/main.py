import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from config.settings import settings
from db.repository import count_stats
from db.session import async_session_factory, init_db
from scrapers import get_all_scrapers
from scheduler.monitor import monitor_service

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
