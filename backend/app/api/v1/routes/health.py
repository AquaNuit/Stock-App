"""Liveness/readiness probes."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter
from sqlalchemy import text

from backend.app.api.deps import CacheDep, ChainDep, DbDep, SettingsDep
from backend.app.schemas.users import HealthResponse, ReadyResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(settings: SettingsDep) -> HealthResponse:
    return HealthResponse(status="ok", version=settings.version, time=datetime.now(UTC))


@router.get("/ready", response_model=ReadyResponse)
def ready(db: DbDep, cache: CacheDep, chain: ChainDep) -> ReadyResponse:
    db_status = "down"
    try:
        db.execute(text("SELECT 1"))
        db_status = "up"
    except Exception:  # noqa: BLE001
        pass
    status = "ready" if db_status == "up" else "degraded"
    return ReadyResponse(status=status, db=db_status, cache=cache.status(), providers=chain.health())
