"""Stock DTOs (docs/api_reference.md)."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class SearchResult(BaseModel):
    symbol: str
    company_name: str
    sector: str = ""
    industry: str = ""
    match_field: str = "symbol"


class StockSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    symbol: str
    company_name: str
    sector: str
    industry: str


class HistoryBar(BaseModel):
    date: date
    open: float
    high: float
    low: float
    close: float
    adj_close: float = 0.0
    volume: int = 0


class HistoryResponse(BaseModel):
    symbol: str
    range: str
    source: str
    count: int
    start: date
    end: date
    bars: list[HistoryBar]
    meta: dict = Field(default_factory=dict)


class StockDetail(BaseModel):
    symbol: str
    company_name: str
    sector: str = ""
    industry: str = ""
    exchange: str = "NSE"
    price: float
    open: float
    high: float
    low: float
    prev_close: float
    change: float
    change_pct: float
    volume: int
    as_of: datetime
    source: str
    # fundamentals (best-effort; source-dependent)
    market_cap: float | None = None
    pe_ratio: float | None = None
    eps: float | None = None
    dividend_yield: float | None = None
    week52_high: float | None = None
    week52_low: float | None = None
