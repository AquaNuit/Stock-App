"""yfinance provider (resilient fallback for NSE symbols via ``.NS`` suffix).

Network-dependent; failures raise ``ProviderError`` so the chain falls through
(ADR-0006). All yfinance interaction is isolated here — importing this module
must never fail on machines with no network, so imports are lazy.
"""

from __future__ import annotations

from datetime import date, datetime

import pandas as pd

from backend.app.core.constants import DataSource
from backend.app.core.logging import get_logger
from backend.app.providers.base import MarketDataProvider, ProviderError, Quote, SymbolInfo

log = get_logger(__name__)

INDEX_TICKERS = {"NIFTY50": "^NSEI", "BANKNIFTY": "^NSEBANK", "SENSEX": "^BSESN", "NIFTYBANK": "^NSEBANK"}


def _to_yf_symbol(symbol: str) -> str:
    symbol = symbol.upper()
    if symbol == "JIOFINANCE":
        return "JIOFIN.NS"
    return INDEX_TICKERS.get(symbol, f"{symbol}.NS")


class YFinanceProvider(MarketDataProvider):
    name = DataSource.YFINANCE
    index_symbols = tuple(INDEX_TICKERS.keys())

    def __init__(self, timeout_s: float = 8.0):
        self.timeout_s = timeout_s

    def list_symbols(self) -> list[SymbolInfo]:
        return []  # yfinance has no universe listing API; discovery comes from DB/seed.

    def get_history(self, symbol: str, start: date | None, end: date | None) -> pd.DataFrame:
        try:
            import yfinance as yf

            ticker = yf.Ticker(_to_yf_symbol(symbol))
            kwargs = {"auto_adjust": False, "timeout": self.timeout_s}
            if start is None and end is None:
                kwargs["period"] = "max"
            else:
                kwargs["start"] = start
                kwargs["end"] = (end + pd.Timedelta(days=1)) if end else None
            
            hist = ticker.history(**kwargs)
        except Exception as exc:  # noqa: BLE001
            raise ProviderError(f"yfinance history failed for {symbol}: {exc}") from exc
        if hist is None or hist.empty:
            raise ProviderError(f"yfinance returned no history for {symbol}")

        hist = hist.reset_index()
        date_col = "Date" if "Date" in hist.columns else hist.columns[0]
        frame = pd.DataFrame(
            {
                "date": pd.to_datetime(hist[date_col]).dt.date,
                "open": hist["Open"].astype(float),
                "high": hist["High"].astype(float),
                "low": hist["Low"].astype(float),
                "close": hist["Close"].astype(float),
                "adj_close": hist.get("Adj Close", hist["Close"]).astype(float),
                "volume": hist["Volume"].fillna(0).astype("int64"),
            }
        ).dropna(subset=["close"])
        if start:
            frame = frame[frame["date"] >= start]
        if end:
            frame = frame[frame["date"] <= end]
        if frame.empty:
            raise ProviderError(f"yfinance empty slice for {symbol}")
        return frame.reset_index(drop=True)

    def get_quotes(self, symbols: list[str]) -> dict[str, Quote]:
        if not symbols:
            return {}
        try:
            import yfinance as yf
            import pandas as pd
            
            yf_symbols = [_to_yf_symbol(s) for s in symbols]
            tickers = " ".join(yf_symbols)
            data = yf.download(tickers, period="5d", group_by="ticker", auto_adjust=False, threads=True, progress=False)
            
            res = {}
            for i, sym in enumerate(symbols):
                yf_sym = yf_symbols[i]
                try:
                    if isinstance(data.columns, pd.MultiIndex):
                        if yf_sym not in data.columns.levels[0]:
                            continue
                        df = data[yf_sym]
                    else:
                        df = data
                        
                    df = df.dropna(subset=["Close"])
                    if df.empty:
                        continue
                        
                    price = float(df["Close"].iloc[-1])
                    prev_close = float(df["Close"].iloc[-2]) if len(df) > 1 else price
                    
                    res[sym.upper()] = Quote(
                        symbol=sym.upper(),
                        price=round(price, 2),
                        open=float(df["Open"].iloc[-1]),
                        high=float(df["High"].iloc[-1]),
                        low=float(df["Low"].iloc[-1]),
                        prev_close=round(prev_close, 2),
                        volume=int(df["Volume"].iloc[-1]),
                        as_of=datetime.now(),
                        source=DataSource.YFINANCE,
                    )
                except Exception as exc:
                    log.debug("yfinance bulk parsing failed for %s: %s", sym, exc)
            return res
        except Exception as exc:
            raise ProviderError(f"yfinance bulk get_quotes failed: {exc}") from exc

    def get_quote(self, symbol: str) -> Quote:
        try:
            import yfinance as yf

            ticker = yf.Ticker(_to_yf_symbol(symbol))
            info = ticker.fast_info  # type: ignore[attr-defined]
            
            price = float(info.last_price) if info.last_price is not None else 0.0
            prev_close = float(info.previous_close) if info.previous_close is not None else price
            
            return Quote(
                symbol=symbol.upper(),
                price=round(price, 2),
                open=float(info.open) if info.open is not None else price,
                high=float(info.day_high) if info.day_high is not None else price,
                low=float(info.day_low) if info.day_low is not None else price,
                prev_close=round(prev_close, 2),
                volume=int(info.last_volume) if info.last_volume is not None else 0,
                as_of=datetime.now(),
                source=DataSource.YFINANCE,
            )
        except Exception as exc:  # noqa: BLE001
            raise ProviderError(f"yfinance quote failed for {symbol}: {exc}") from exc
