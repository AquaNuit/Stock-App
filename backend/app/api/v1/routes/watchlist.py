"""Watchlist + user recents."""

from __future__ import annotations

from fastapi import APIRouter, Query

from backend.app.api.deps import UserDep, WatchlistServiceDep
from backend.app.schemas.users import SearchHistoryRow, WatchlistAddRequest, WatchlistResponse

router = APIRouter(tags=["watchlist", "users"])


@router.get("/watchlist", response_model=WatchlistResponse)
def get_watchlist(svc: WatchlistServiceDep, user: UserDep) -> WatchlistResponse:
    return svc.list(user)


@router.post("/watchlist", response_model=WatchlistResponse, status_code=201)
def add_to_watchlist(body: WatchlistAddRequest, svc: WatchlistServiceDep, user: UserDep) -> WatchlistResponse:
    return svc.add(user, body.symbol)


@router.delete("/watchlist/{symbol}", response_model=WatchlistResponse)
def remove_from_watchlist(symbol: str, svc: WatchlistServiceDep, user: UserDep) -> WatchlistResponse:
    return svc.remove(user, symbol)


@router.get("/users/me/searches", response_model=dict)
def recent_searches(
    svc: WatchlistServiceDep, user: UserDep, limit: int = Query(default=10, ge=1, le=25)
) -> dict:
    rows: list[SearchHistoryRow] = svc.recent_searches(user, limit=limit)
    return {"items": [r.model_dump(mode="json") for r in rows], "count": len(rows)}
