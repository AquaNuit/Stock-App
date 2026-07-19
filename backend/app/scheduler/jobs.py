"""APScheduler background jobs (docs/ml_pipeline.md §9; Celery upgrade = R2.7).

Jobs: post-EOD price refresh (Mon–Fri 15:45 IST) and nightly incremental
retraining of watchlisted symbols (21:30 IST).
"""

from __future__ import annotations

from datetime import UTC, date, datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from backend.app.core.config import Settings, get_settings
from backend.app.core.logging import get_logger
from backend.app.database.session import session_scope
from backend.app.providers import default_chain
from backend.app.repositories import PriceRepository, StockRepository, TrainingRunRepository
from backend.app.services.stock_service import StockService
from backend.app.services.watchlist_service import WatchlistService

log = get_logger(__name__)
_scheduler: BackgroundScheduler | None = None


def refresh_prices(settings: Settings | None = None) -> int:
    """Pull the latest bars for every universe symbol and upsert."""
    settings = settings or get_settings()
    chain = default_chain(settings)
    updated = 0
    with session_scope(settings) as session:
        stocks = StockRepository(session)
        prices = PriceRepository(session)
        for stock in stocks.list_all(limit=10_000):
            try:
                latest = prices.latest_date(stock.id)
                if latest is not None and latest >= date.today():
                    continue
                frame, source = chain.get_history(stock.symbol, None, None)
                updated += prices.bulk_upsert(stock.id, frame.tail(45), source=source.value)
            except Exception as exc:  # noqa: BLE001
                log.warning("refresh failed for %s: %s", stock.symbol, exc)
                session.rollback()
    log.info("refresh_prices complete: %d rows upserted", updated)
    return updated


def retrain_watchlisted(settings: Settings | None = None) -> int:
    """Incremental retrain: only symbols with data newer than their last successful run."""
    settings = settings or get_settings()
    chain = default_chain(settings)
    retrained = 0
    with session_scope(settings) as session:
        wl = WatchlistService(session, chain)
        watch = wl.list("guest")
        # Also include any user's watchlist (single-user MVP → union of all users' lists).
        from backend.app.repositories import UserRepository

        for user in UserRepository(session).list(limit=1000):
            for row in wl.list(user.external_id).items:
                if row.symbol not in {r.symbol for r in watch.items}:
                    watch.items.append(row)
        stock_svc = StockService(session, chain)
        prices = PriceRepository(session)
        runs = TrainingRunRepository(session)
        stocks = StockRepository(session)
        for row in watch.items:
            try:
                stock = stocks.by_symbol(row.symbol)
                if stock is None:
                    continue
                latest_price = prices.latest_date(stock.id)
                recent = runs.recent_runs(stock.id, limit=1)
                last_run = recent[0].finished_at if recent else None
                last_run_date = last_run.date() if last_run else None
                if latest_price and last_run_date and latest_price <= last_run_date:
                    continue  # nothing new to learn
                svc = stock_svc
                from backend.app.services.prediction_service import PredictionService

                PredictionService(session, svc, settings=settings).forecast7(row.symbol, "2y", force_retrain=True)
                runs.prune_runs(stock.id, keep_last=3)
                retrained += 1
            except Exception as exc:  # noqa: BLE001
                log.warning("retrain failed for %s: %s", row.symbol, exc)
                session.rollback()
    log.info("retrain_watchlisted complete: %d symbols retrained", retrained)
    return retrained


def start_scheduler(settings: Settings | None = None) -> BackgroundScheduler | None:
    global _scheduler
    settings = settings or get_settings()
    if not settings.scheduler_enabled:
        log.info("scheduler disabled (SCHEDULER_ENABLED=false)")
        return None
    if _scheduler is not None:
        return _scheduler
    sched = BackgroundScheduler(timezone="Asia/Kolkata")
    sched.add_job(refresh_prices, CronTrigger(day_of_week="mon-fri", hour=15, minute=45), id="refresh_prices")
    sched.add_job(
        retrain_watchlisted, CronTrigger(day_of_week="mon-fri", hour=21, minute=30), id="retrain_watchlisted"
    )
    sched.start()
    _scheduler = sched
    log.info("scheduler started: jobs=%s at %s", [j.id for j in sched.get_jobs()], datetime.now(UTC).isoformat())
    return sched


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
