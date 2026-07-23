"""FastAPI application factory (composition root for the HTTP runtime).

Run: ``uvicorn backend.app.main:app --reload`` (see docs/deployment.md §4).
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.errors import register_error_handlers
from backend.app.api.middleware import RateLimitMiddleware, RequestIDMiddleware, TimingMiddleware
from backend.app.api.v1.router import api_router
from backend.app.core.config import get_settings
from backend.app.core.constants import API_V1_PREFIX
from backend.app.core.logging import configure_logging, get_logger
from backend.app.database.session import init_db

log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[no-untyped-def]
    settings = app.state.settings
    configure_logging(settings.log_level)
    init_db(settings)
    # Idempotent universe seed → search/autocomplete works immediately.
    try:
        from backend.app.api.deps import get_chain
        from backend.app.database.session import session_scope
        from backend.app.services.stock_service import StockService

        with session_scope(settings) as session:
            added = StockService(session, get_chain()).ensure_universe_seeded()
            if added:
                log.info("universe seeded: %d new symbols", added)
    except Exception as exc:  # noqa: BLE001
        log.warning("universe seeding skipped: %s", exc)
    scheduler = None
    try:
        from backend.app.scheduler.jobs import start_scheduler

        scheduler = start_scheduler(settings)
    except Exception as exc:  # noqa: BLE001
        log.warning("scheduler failed to start: %s", exc)
    yield
    if scheduler is not None:
        from backend.app.scheduler.jobs import stop_scheduler

        stop_scheduler()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="StockSense AI",
        version=settings.version,
        description="AI-powered NSE stock analysis and 7-day forecasting platform.",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )
    app.state.settings = settings

    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(TimingMiddleware)
    app.add_middleware(RateLimitMiddleware, settings=settings)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_error_handlers(app)
    app.include_router(api_router, prefix=API_V1_PREFIX)

    # UptimeRobot keep-alive endpoint (root level for easy pinging)
    @app.api_route("/ping", methods=["GET", "HEAD"], tags=["uptime"])
    @app.api_route("/", methods=["GET", "HEAD"], tags=["uptime"])
    async def root_ping() -> dict:
        from datetime import UTC, datetime
        return {"status": "ok", "service": "stocksense-ai", "time": datetime.now(UTC).isoformat()}

    return app


app = create_app()


def main() -> None:  # entry point for `stocksense-api`
    import uvicorn

    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    main()
