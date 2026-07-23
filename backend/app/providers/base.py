"""Market-data provider contract.

Providers return **data only** — persistence and caching concerns live in the
``ProviderChain`` and services (docs/architecture.md §5.1).
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from datetime import date, datetime

import pandas as pd

from backend.app.core.constants import DataSource


@dataclass(slots=True, frozen=True)
class SymbolInfo:
    symbol: str
    company_name: str
    sector: str = ""
    industry: str = ""
    exchange: str = "NSE"


@dataclass(slots=True)
class Quote:
    symbol: str
    price: float
    open: float
    high: float
    low: float
    prev_close: float
    volume: int
    as_of: datetime
    source: DataSource
    change: float = field(init=False)
    change_pct: float = field(init=False)

    def __post_init__(self) -> None:
        self.change = round(self.price - self.prev_close, 2)
        self.change_pct = round((self.change / self.prev_close) * 100, 4) if self.prev_close else 0.0


class MarketDataProvider(abc.ABC):
    """Ordered-provider-chain member (ADR-0006). Implementations must be side-effect free."""

    name: DataSource = DataSource.SEED
    timeout_s: float = 8.0
    index_symbols: tuple[str, ...] = ()

    @abc.abstractmethod
    def list_symbols(self) -> list[SymbolInfo]:
        """Universe known to the provider (may be empty for quote-only providers)."""

    @abc.abstractmethod
    def get_history(self, symbol: str, start: date | None, end: date | None) -> pd.DataFrame:
        """OHLCV DataFrame with columns [date, open, high, low, close, adj_close, volume] ascending by date.
        Must raise ``ProviderUnavailableError`` when it cannot serve the request (chain falls through)."""

    @abc.abstractmethod
    def get_quote(self, symbol: str) -> Quote:
        """Latest quote (approximation from last bars is acceptable for EOD providers)."""

    def get_quotes(self, symbols: list[str]) -> dict[str, Quote]:
        """Bulk latest quotes. Base implementation falls back to sequential get_quote calls."""
        res = {}
        for sym in symbols:
            try:
                res[sym] = self.get_quote(sym)
            except ProviderError:
                pass
        return res

    def supports(self, symbol: str) -> bool:  # noqa: ARG002 - overridable filter
        return True


class ProviderError(Exception):
    """Internal marker — the chain converts it to fall-through behavior."""
