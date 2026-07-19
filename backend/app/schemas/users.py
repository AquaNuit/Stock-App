"""User/watchlist/search-history DTOs (header-identity MVP — ADR-0011)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class WatchlistAddRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=20)


class WatchlistRow(BaseModel):
    symbol: str
    company_name: str
    price: float | None
    change_pct: float | None
    added_at: datetime
    latest_forecast_change_pct: float | None = None


class WatchlistResponse(BaseModel):
    user: str
    count: int
    items: list[WatchlistRow]


class SearchHistoryRow(BaseModel):
    query: str
    matched_symbol: str
    created_at: datetime


class HealthResponse(BaseModel):
    status: str
    version: str
    time: datetime


class ReadyResponse(BaseModel):
    status: str
    db: str
    cache: dict
    providers: dict
