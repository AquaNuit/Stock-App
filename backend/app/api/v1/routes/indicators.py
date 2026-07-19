"""Technical indicator endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Query

from backend.app.api.deps import IndicatorServiceDep
from backend.app.schemas.insights import IndicatorSnapshot

router = APIRouter(prefix="/indicators", tags=["indicators"])


@router.get("/{symbol}", response_model=IndicatorSnapshot)
def indicators(
    symbol: str,
    svc: IndicatorServiceDep,
    range: str = Query(default="6m", pattern="^(1m|3m|6m|1y|2y|5y|max)$"),
) -> IndicatorSnapshot:
    return svc.snapshot(symbol, range)
