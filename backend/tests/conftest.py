"""Shared fixtures: isolated SQLite DB, seed-only provider chain, app client.

Environment is pinned BEFORE any backend import so ``get_settings`` (lru_cache)
picks it up exactly once.
"""

from __future__ import annotations

import os
import tempfile
import warnings

warnings.filterwarnings("ignore")

_tmp = tempfile.mkdtemp(prefix="stocksense_test_")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["SCHEDULER_ENABLED"] = "false"
os.environ["NSE_ENABLED"] = "false"  # hermetic tests: seed-only chain
os.environ["RATE_LIMIT_PER_MINUTE"] = "0"  # disable limiter in tests
os.environ["CORS_ORIGINS"] = "http://localhost"

import pytest  # noqa: E402

from backend.app.core.config import get_settings  # noqa: E402


@pytest.fixture(scope="session")
def settings():
    return get_settings()


@pytest.fixture(scope="session")
def _bootstrapped(settings):
    """Init schema + seed universe once per test session."""
    from backend.app.database import models  # noqa: F401
    from backend.app.database.session import get_session_factory, init_db, reset_global_state

    reset_global_state()
    init_db(settings)
    factory = get_session_factory(settings)
    session = factory()
    try:
        from sqlalchemy import select

        from backend.app.database.models import Stock
        from backend.app.services.stock_service import StockService
        from backend.tests.fakes import seed_only_chain

        exists = session.scalar(select(Stock.symbol).limit(1))
        if not exists:
            StockService(session, seed_only_chain(settings)).ensure_universe_seeded()
        yield settings
    finally:
        session.close()


@pytest.fixture()
def session(settings, _bootstrapped):
    from backend.app.database.session import get_session_factory

    factory = get_session_factory(settings)
    sess = factory()
    try:
        yield sess
    finally:
        sess.rollback()
        sess.close()


@pytest.fixture(scope="session")
def chain(settings):
    from backend.tests.fakes import seed_only_chain

    return seed_only_chain(settings)


@pytest.fixture(scope="session")
def client(settings, _bootstrapped):
    from fastapi.testclient import TestClient

    from backend.app.main import create_app

    app = create_app()
    with TestClient(app) as c:
        yield c
