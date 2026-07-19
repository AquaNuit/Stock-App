"""AI insights endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from backend.app.api.deps import InsightsServiceDep
from backend.app.schemas.insights import InsightsResponse

router = APIRouter(prefix="/insights", tags=["insights"])


@router.get("/{symbol}", response_model=InsightsResponse)
def insights(symbol: str, svc: InsightsServiceDep) -> InsightsResponse:
    return svc.generate(symbol)
