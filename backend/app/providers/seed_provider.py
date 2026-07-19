"""Deterministic seed-data provider — the chain's final fallback (ADR-0007).

Produces stable, regime-aware random-walk OHLCV for every symbol in the curated
universe. Properties:
- fully deterministic (seeded by SHA-256 of the symbol),
- business-day index, sane OHLC invariants (low ≤ open/close ≤ high),
- volume correlated with |return| like real equity tape,
- clearly labeled ``source=seed`` everywhere it surfaces.
"""

from __future__ import annotations

import hashlib
from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd

from backend.app.core.constants import DataSource
from backend.app.data.seed.nse_universe import INDEX_META, NSE_UNIVERSE
from backend.app.providers.base import MarketDataProvider, ProviderError, Quote, SymbolInfo

GENESIS = date(2015, 1, 1)

# Plausible recent price anchors for high-profile tickers (approximate, not live).
ANCHORS: dict[str, float] = {
    "RELIANCE": 2850.0, "TCS": 4200.0, "HDFCBANK": 1720.0, "INFY": 1650.0,
    "ICICIBANK": 1180.0, "SBIN": 820.0, "BHARTIARTL": 1560.0, "ITC": 470.0,
    "KOTAKBANK": 1780.0, "LT": 3650.0, "AXISBANK": 1120.0, "HINDUNILVR": 2480.0,
    "MRF": 128000.0, "PAGEIND": 36000.0, "HONAUT": 42000.0, "SHREECEM": 26000.0,
    "BOSCHLTD": 31000.0, "ABB": 7600.0, "TITAN": 3420.0, "ASIANPAINT": 2950.0,
    "MARUTI": 12200.0, "NESTLEIND": 2440.0, "ULTRACEMCO": 10900.0, "DMART": 3980.0,
    "TRENT": 5100.0, "BAJFINANCE": 6900.0, "EICHERMOT": 4800.0, "ADANIENT": 2950.0,
}


def _rng(symbol: str) -> np.random.Generator:
    seed = int(hashlib.sha256(f"stocksense::{symbol}".encode()).hexdigest()[:16], 16)
    return np.random.default_rng(np.random.SeedSequence(seed))


def generate_series(symbol: str, end: date | None = None, years: float = 11.0) -> pd.DataFrame:
    """Deterministic OHLCV frame for ``symbol`` ending at ``end`` (default: today)."""
    symbol = symbol.upper()
    end = end or date.today()
    n_days = int(years * 365.25)
    start = end - timedelta(days=n_days)
    days = pd.bdate_range(start=start, end=end)  # business days ≈ trading days
    n = len(days)
    if n < 30:
        raise ProviderError(f"not enough business days generated for {symbol}")

    rng = _rng(symbol)
    # Per-symbol structural params, stable across runs.
    base_price = ANCHORS.get(symbol, float(rng.uniform(180, 4200)))
    annual_drift = float(rng.uniform(0.04, 0.22))
    annual_vol = float(rng.uniform(0.16, 0.42))
    jumpiness = float(rng.uniform(0.0, 0.03))

    dt = 1 / 252
    drift = (annual_drift - 0.5 * annual_vol**2) * dt
    shocks = rng.standard_normal(n)
    sigma = annual_vol * np.sqrt(dt)
    diffusion = sigma * shocks
    # Weak AR(1) structure — real equity returns contain small learnable
    # autocorrelation that trend/momentum models should pick up.
    ar1 = float(rng.uniform(0.05, 0.14))
    ar_component = np.zeros(n)
    ar_component[1:] = ar1 * shocks[:-1] * sigma
    jumps = rng.choice([0.0, 1.0, -1.0], size=n, p=[1 - jumpiness, jumpiness / 2, jumpiness / 2])
    jump_sizes = jumps * rng.uniform(0.02, 0.06, size=n)
    # Smooth regime cycles so charts show drawdowns/rallies (not pure noise).
    regime = np.sin(np.linspace(0, rng.uniform(4, 14), n) + rng.uniform(0, 3)) * 0.0012
    log_ret = drift + diffusion + ar_component + jump_sizes + regime

    # Anchor the *last* close to base_price by walking backwards.
    close = base_price * np.exp(-np.cumsum(log_ret[::-1])[::-1] + log_ret)
    open_ = close * np.exp(-np.roll(log_ret, 1))  # previous close
    open_[0] = close[0] * np.exp(-log_ret[0])
    spread = np.abs(rng.normal(0.006, 0.004, size=n))
    high = np.maximum(open_, close) * (1 + spread)
    low = np.minimum(open_, close) * (1 - spread * rng.uniform(0.6, 1.0, size=n))

    base_volume = rng.uniform(2e5, 3e6)
    volume = (
        base_volume
        * (1.0 + 6.0 * np.abs(diffusion))
        * rng.lognormal(mean=0.0, sigma=0.35, size=n)
    ).astype(np.int64)

    return pd.DataFrame(
        {
            "date": days.date,
            "open": np.round(open_, 2),
            "high": np.round(high, 2),
            "low": np.round(low, 2),
            "close": np.round(close, 2),
            "adj_close": np.round(close, 2),
            "volume": volume,
        }
    )


def generate_index_series(index_key: str, end: date | None = None) -> pd.DataFrame:
    """Synthetic index = basket composite, last value anchored to a plausible level."""
    meta = INDEX_META[index_key]
    end = end or date.today()
    closes = {}
    for member in meta["basket"]:
        try:
            frame = generate_series(member, end=end)
        except ProviderError:
            continue
        closes[member] = np.log(frame["close"].to_numpy()).astype("float64")
    if not closes:
        raise ProviderError(f"index {index_key} has no members")
    log_index = np.mean(list(closes.values()), axis=0)
    last_close = meta["base"] * (1 + 0.001 * (len(log_index) % 7))
    scale = np.log(last_close) - log_index[-1]
    close = np.exp(log_index + scale)
    prev = np.roll(close, 1)
    prev[0] = close[0]
    frame = generate_series(meta["basket"][0], end=end)  # only for the calendar/volume template
    rng = _rng(index_key)
    spread = np.abs(rng.normal(0.004, 0.002, size=len(close)))
    return pd.DataFrame(
        {
            "date": frame["date"].to_numpy(),
            "open": np.round(prev, 2),
            "high": np.round(np.maximum(prev, close) * (1 + spread), 2),
            "low": np.round(np.minimum(prev, close) * (1 - spread), 2),
            "close": np.round(close, 2),
            "adj_close": np.round(close, 2),
            "volume": np.full(len(close), 0, dtype=np.int64),
        }
    )


class SeedDataProvider(MarketDataProvider):
    """Offline-capable provider over the curated universe (always available)."""

    name = DataSource.SEED
    index_symbols = tuple(INDEX_META.keys())

    def __init__(self, universe: list[tuple[str, str, str, str]] | None = None):
        rows = universe or NSE_UNIVERSE
        self._universe = {
            s: SymbolInfo(symbol=s, company_name=name, sector=sector, industry=industry)
            for s, name, sector, industry in rows
        }
        self._cache: dict[str, pd.DataFrame] = {}

    def list_symbols(self) -> list[SymbolInfo]:
        return list(self._universe.values())

    def supports(self, symbol: str) -> bool:
        return symbol.upper() in self._universe or symbol.upper() in INDEX_META

    def _series(self, symbol: str) -> pd.DataFrame:
        if symbol not in self._cache:
            if symbol in INDEX_META:
                self._cache[symbol] = generate_index_series(symbol)
            elif symbol in self._universe:
                self._cache[symbol] = generate_series(symbol)
            else:
                raise ProviderError(f"seed provider has no {symbol}")
        return self._cache[symbol]

    def get_history(self, symbol: str, start: date | None, end: date | None) -> pd.DataFrame:
        symbol = symbol.upper()
        frame = self._series(symbol)
        if start is not None:
            frame = frame[frame["date"] >= start]
        if end is not None:
            frame = frame[frame["date"] <= end]
        if frame.empty:
            raise ProviderError(f"seed provider: empty slice for {symbol}")
        return frame.reset_index(drop=True)

    def get_quote(self, symbol: str) -> Quote:
        symbol = symbol.upper()
        frame = self._series(symbol)
        last = frame.iloc[-1]
        prev_close = float(frame.iloc[-2]["close"]) if len(frame) > 1 else float(last["open"])
        return Quote(
            symbol=symbol,
            price=float(last["close"]),
            open=float(last["open"]),
            high=float(last["high"]),
            low=float(last["low"]),
            prev_close=prev_close,
            volume=int(last["volume"]),
            as_of=datetime.combine(last["date"], datetime.min.time()),
            source=DataSource.SEED,
        )
