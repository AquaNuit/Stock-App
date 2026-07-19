"""NSE first-party provider (official endpoints where reachable — ADR-0006).

Strategy, in order:
1. ``nselib`` capital-market historical API (structured, maintained client).
2. Direct NSE chart/equity JSON API via httpx with cookie priming + browser headers.
3. ``nsepython`` equity_history as last in-provider option.

Any failure raises ``ProviderError`` so the chain falls through to yfinance.
NSE endpoints are rate-limited and cookie-gated; this provider is intentionally
defensive and disabled via ``NSE_ENABLED=false``.
"""

from __future__ import annotations

from datetime import date, datetime

import pandas as pd

from backend.app.core.constants import DataSource
from backend.app.core.logging import get_logger
from backend.app.providers.base import MarketDataProvider, ProviderError, Quote, SymbolInfo

log = get_logger(__name__)

_BASE = "https://www.nseindia.com"
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/get-quotes/equity",
}


class NSEProvider(MarketDataProvider):
    name = DataSource.NSE

    def __init__(self, timeout_s: float = 8.0, enabled: bool = True):
        self.timeout_s = timeout_s
        self.enabled = enabled

    def list_symbols(self) -> list[SymbolInfo]:
        return []  # universe sync job is a roadmap item (R1.7)

    # -- public API ----------------------------------------------------------
    def get_history(self, symbol: str, start: date | None, end: date | None) -> pd.DataFrame:
        self._guard()
        symbol = symbol.upper()
        for fetch in (self._via_nselib, self._via_chart_api, self._via_nsepython):
            try:
                frame = fetch(symbol, start, end)
            except ProviderError:
                continue
            except Exception as exc:  # noqa: BLE001
                log.debug("nse %s failed for %s: %s", fetch.__name__, symbol, exc)
                continue
            if frame is not None and not frame.empty:
                return self._slice(frame, start, end)
        raise ProviderError(f"all NSE strategies failed for {symbol}")

    def get_quote(self, symbol: str) -> Quote:
        self._guard()
        frame = self.get_history(symbol.upper(), None, None)
        tail = frame.tail(2)
        last, prev = tail.iloc[-1], (tail.iloc[-2] if len(tail) > 1 else tail.iloc[-1])
        return Quote(
            symbol=symbol.upper(),
            price=float(last["close"]),
            open=float(last["open"]),
            high=float(last["high"]),
            low=float(last["low"]),
            prev_close=float(prev["close"]),
            volume=int(last["volume"]),
            as_of=datetime.combine(last["date"], datetime.min.time()),
            source=DataSource.NSE,
        )

    # -- strategies -----------------------------------------------------------
    def _via_nselib(self, symbol: str, start: date | None, end: date | None) -> pd.DataFrame:
        import nselib  # type: ignore[import-not-found]  # optional dependency
        from nselib import capital_market

        end = end or date.today()
        start = start or (date(end.year - 1, end.month, end.day) if end.year > 2000 else end)
        df = capital_market.price_volume_and_deliverable_position_data(
            symbol=symbol, from_date=start.strftime("%d-%m-%Y"), to_date=end.strftime("%d-%m-%Y")
        )
        if df is None or df.empty:
            raise ProviderError("nselib returned empty frame")
        cols = {c.lower(): c for c in df.columns}
        frame = pd.DataFrame(
            {
                "date": pd.to_datetime(df[cols.get("date", "Date")], dayfirst=True, errors="coerce").dt.date,
                "open": pd.to_numeric(df[cols.get("openprice", cols.get("open", "OpenPrice"))], errors="coerce"),
                "high": pd.to_numeric(df[cols.get("highprice", cols.get("high", "HighPrice"))], errors="coerce"),
                "low": pd.to_numeric(df[cols.get("lowprice", cols.get("low", "LowPrice"))], errors="coerce"),
                "close": pd.to_numeric(df[cols.get("closeprice", cols.get("close", "ClosePrice"))], errors="coerce"),
                "volume": pd.to_numeric(
                    df[cols.get("totaltradedquantity", cols.get("volume", "TotalTradedQuantity"))],
                    errors="coerce",
                ),
            }
        ).dropna(subset=["close"])
        frame["adj_close"] = frame["close"]
        frame["volume"] = frame["volume"].fillna(0).astype("int64")
        return frame.sort_values("date").reset_index(drop=True)

    def _via_chart_api(self, symbol: str, start: date | None, end: date | None) -> pd.DataFrame:
        import httpx

        with httpx.Client(headers=_HEADERS, timeout=self.timeout_s, follow_redirects=True) as client:
            client.get(_BASE)  # cookie priming
            resp = client.get(f"{_BASE}/api/chart-databyindex", params={"index": f"{symbol}EQN"})
            resp.raise_for_status()
            payload = resp.json()
        points = payload.get("grapthData") or payload.get("graphData") or []
        if not points:
            raise ProviderError("chart api returned no points")
        frame = pd.DataFrame(
            {
                "date": pd.to_datetime([p[0] for p in points], unit="ms").date,
                "close": [float(p[1]) for p in points],
            }
        )
        frame["open"] = frame["high"] = frame["low"] = frame["adj_close"] = frame["close"]
        frame["volume"] = 0
        return frame

    def _via_nsepython(self, symbol: str, start: date | None, end: date | None) -> pd.DataFrame:
        from nsepython import equity_history  # type: ignore[import-not-found]  # optional dependency

        end = end or date.today()
        start = start or date(end.year - 1, end.month, end.day)
        raw = equity_history(
            symbol, "EQ", start.strftime("%d-%m-%Y"), end.strftime("%d-%m-%Y")
        )
        df = pd.DataFrame(raw)
        if df.empty or "CH_CLOSING_PRICE" not in df.columns:
            raise ProviderError("nsepython returned empty frame")
        frame = pd.DataFrame(
            {
                "date": pd.to_datetime(df["CH_TIMESTAMP"]).dt.date,
                "open": pd.to_numeric(df["CH_OPENING_PRICE"], errors="coerce"),
                "high": pd.to_numeric(df["CH_TRADE_HIGH_PRICE"], errors="coerce"),
                "low": pd.to_numeric(df["CH_TRADE_LOW_PRICE"], errors="coerce"),
                "close": pd.to_numeric(df["CH_CLOSING_PRICE"], errors="coerce"),
                "adj_close": pd.to_numeric(df.get("CH_CLOSING_PRICE"), errors="coerce"),
                "volume": pd.to_numeric(df["CH_TOT_TRADED_QTY"], errors="coerce").fillna(0).astype("int64"),
            }
        ).dropna(subset=["close"])
        return frame.sort_values("date").reset_index(drop=True)

    # -- helpers ----------------------------------------------------------------
    def _guard(self) -> None:
        if not self.enabled:
            raise ProviderError("NSE provider disabled (NSE_ENABLED=false)")

    @staticmethod
    def _slice(frame: pd.DataFrame, start: date | None, end: date | None) -> pd.DataFrame:
        if start:
            frame = frame[frame["date"] >= start]
        if end:
            frame = frame[frame["date"] <= end]
        if frame.empty:
            raise ProviderError("slice empty after filtering")
        return frame.reset_index(drop=True)
