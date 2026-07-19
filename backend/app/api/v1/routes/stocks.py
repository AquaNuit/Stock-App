"""Stock search, detail, history."""

from __future__ import annotations

from fastapi import APIRouter, Query

from backend.app.api.deps import StockServiceDep, UserDep, WatchlistServiceDep
from backend.app.database.models import Stock
from backend.app.schemas.stocks import HistoryResponse, SearchResult, StockDetail, StockSummary

router = APIRouter(prefix="/stocks", tags=["stocks"])


@router.get("/search", response_model=dict)
def search(
    svc: StockServiceDep,
    watchlist: WatchlistServiceDep,
    user: UserDep,
    q: str = Query(min_length=1, max_length=60),
    limit: int = Query(default=10, ge=1, le=25),
) -> dict:
    results = svc.search(q, limit=limit)
    matched = results[0].symbol if results and results[0].symbol.upper() == q.strip().upper() else ""
    try:
        watchlist.record_search(user, q, matched)
    except Exception:  # noqa: BLE001 — telemetry must never block search
        pass
    return {"items": [r.model_dump() for r in results], "count": len(results)}


@router.get("", response_model=dict)
def list_stocks(
    svc: StockServiceDep,
    sector: str | None = Query(default=None, max_length=80),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> dict:
    rows: list[Stock] = svc.stocks.list_all(sector=sector, limit=limit, offset=offset)
    items = [StockSummary.model_validate(r).model_dump() for r in rows]
    return {"items": items, "count": len(items)}


@router.get("/{symbol}", response_model=StockDetail)
def detail(symbol: str, svc: StockServiceDep) -> StockDetail:
    return svc.details(symbol)


@router.get("/{symbol}/history", response_model=HistoryResponse)
def history(
    symbol: str,
    svc: StockServiceDep,
    range: str = Query(default="1y", pattern="^(1m|3m|6m|1y|2y|5y|max)$"),
) -> HistoryResponse:
    return svc.history(symbol, range)
