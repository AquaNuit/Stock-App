"""Market overview DTOs."""

from __future__ import annotations

from pydantic import BaseModel


class IndexQuote(BaseModel):
    key: str
    name: str
    value: float
    change: float
    change_pct: float
    spark: list[float]  # last ~30 closes, normalized for sparklines
    source: str


class MarketOverview(BaseModel):
    indices: list[IndexQuote]
    advancers: int
    decliners: int
    unchanged: int
    sentiment_score: float  # 0–100 (% of universe above its 20d mean)
    sentiment_label: str
    source: str


class MoverRow(BaseModel):
    symbol: str
    company_name: str
    price: float
    change: float
    change_pct: float
    volume: int


class MoversResponse(BaseModel):
    kind: str
    count: int
    source: str
    items: list[MoverRow]
