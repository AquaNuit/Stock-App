"""Engine/session factories (SQLite dev → PostgreSQL prod via DATABASE_URL).

Synchronous SQLAlchemy 2.0 — see ADR-0012. FastAPI calls repositories from the
threadpool (``def`` endpoints), so no event-loop blocking.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.config import Settings, get_settings
from backend.app.core.logging import get_logger

log = get_logger(__name__)


def get_engine(settings: Settings | None = None) -> Engine:
    """Build (or reuse) the global engine."""
    global _engine
    settings = settings or get_settings()
    if _engine is not None and str(_engine.url) == _normalize(settings.database_url):
        return _engine
    url = _normalize(settings.database_url)
    kwargs: dict = {"pool_pre_ping": True, "future": True}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    else:
        kwargs["pool_size"] = settings.db_pool_size
        kwargs["max_overflow"] = settings.db_pool_size
    _engine = create_engine(url, **kwargs)
    if url.startswith("sqlite"):
        _apply_sqlite_pragmas(_engine)
    log.info("db engine ready url=%s", _redact(url))
    return _engine


def _normalize(url: str) -> str:
    # Allow shorthand `postgres://` (Railway/Render style).
    return url.replace("postgres://", "postgresql+psycopg://", 1)


def _redact(url: str) -> str:
    return url.split("@")[-1] if "@" in url else url


def _apply_sqlite_pragmas(engine: Engine) -> None:
    @event.listens_for(engine, "connect")
    def _set_pragmas(dbapi_conn, _):  # type: ignore[no-untyped-def]
        cur = dbapi_conn.cursor()
        for stmt in ("PRAGMA journal_mode=WAL", "PRAGMA synchronous=NORMAL", "PRAGMA foreign_keys=ON"):
            cur.execute(stmt)
        cur.close()


_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def get_session_factory(settings: Settings | None = None) -> sessionmaker[Session]:
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(bind=get_engine(settings), expire_on_commit=False, autoflush=False)
    return _session_factory


@contextmanager
def session_scope(settings: Settings | None = None) -> Iterator[Session]:
    """Transactional scope for scripts/services outside the request cycle."""
    factory = get_session_factory(settings)
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db(settings: Settings | None = None) -> None:
    """Create tables (dev convenience — Alembic in R5.5)."""
    from backend.app.database import models  # noqa: F401  (register models)

    engine = get_engine(settings)
    from backend.app.database.base import Base

    Base.metadata.create_all(engine)
    log.info("db schema ensured")


def reset_global_state() -> None:
    """Testing hook: drop cached engine/session so temp URLs apply."""
    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _session_factory = None
