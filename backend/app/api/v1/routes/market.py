"""Market overview + movers."""

from __future__ import annotations

from fastapi import APIRouter, Query

from backend.app.api.deps import MarketServiceDep
from backend.app.schemas.market import MarketOverview, MoversResponse

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/overview", response_model=MarketOverview)
def overview(svc: MarketServiceDep) -> MarketOverview:
    return svc.overview()


@router.get("/movers", response_model=MoversResponse)
def movers(
    svc: MarketServiceDep,
    kind: str = Query(default="gainers", pattern="^(gainers|losers|active)$"),
    limit: int = Query(default=10, ge=1, le=50),
) -> MoversResponse:
    return svc.movers(kind, limit=limit)
