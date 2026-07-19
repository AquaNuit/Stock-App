"""Technical indicators (docs/ml_pipeline.md §3) — vectorized, no look-ahead.

Every column at row ``t`` uses only data at or before ``t``.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

SMA_WINDOWS = (5, 10, 20, 50, 100, 200)
EMA_SPANS = (12, 26)


def _rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Wilder-smoothed RSI."""
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0.0, np.nan)
    return (100 - 100 / (1 + rs)).fillna(50.0)


def _atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    prev_close = df["close"].shift(1)
    tr = pd.concat(
        [
            df["high"] - df["low"],
            (df["high"] - prev_close).abs(),
            (df["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()


def add_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Append the full indicator catalog to a cleaned OHLCV frame (returns a copy)."""
    out = df.copy()
    close, high, low, volume = out["close"], out["high"], out["low"], out["volume"]
    log_ret_1 = np.log(close / close.shift(1))

    # Trend — ratios keep features stationary across price regimes.
    for w in SMA_WINDOWS:
        out[f"sma_{w}"] = close.rolling(w, min_periods=max(5, w // 2)).mean()
        out[f"close_over_sma_{w}"] = close / out[f"sma_{w}"]
    for s in EMA_SPANS:
        out[f"ema_{s}"] = close.ewm(span=s, adjust=False, min_periods=s).mean()
    out["ema_cross_12_26"] = out["ema_12"] / out["ema_26"]

    # Momentum
    out["rsi_14"] = _rsi(close)
    macd = out["ema_12"] - out["ema_26"]
    out["macd"] = macd
    out["macd_signal"] = macd.ewm(span=9, adjust=False, min_periods=9).mean()
    out["macd_hist"] = out["macd"] - out["macd_signal"]
    for w in (5, 10, 21):
        out[f"roc_{w}"] = close.pct_change(periods=w, fill_method=None)
        out[f"mom_{w}"] = close - close.shift(w)

    # Volatility
    out["atr_14"] = _atr(out)
    out["atr_pct"] = out["atr_14"] / close
    ma20 = close.rolling(20, min_periods=10).mean()
    sd20 = close.rolling(20, min_periods=10).std(ddof=0)
    out["bb_width"] = (4 * sd20) / ma20
    out["bb_pct_b"] = (close - (ma20 - 2 * sd20)) / (4 * sd20)
    for w in (10, 21):
        out[f"vol_{w}"] = log_ret_1.rolling(w, min_periods=max(5, w // 2)).std() * np.sqrt(252)

    # Volume
    typical = (high + low + close) / 3
    pv = typical * volume
    roll_pv = pv.rolling(20, min_periods=5).sum()
    roll_v = volume.rolling(20, min_periods=5).sum().replace(0, np.nan)
    out["vwap_20"] = roll_pv / roll_v  # rolling-VWAP approximation for EOD data
    out["close_over_vwap"] = close / out["vwap_20"]
    direction = np.sign(close.diff()).fillna(0.0)
    out["obv"] = (direction * volume).cumsum()
    out["obv_slope_10"] = out["obv"].diff(10)
    out["vol_change_1"] = volume.pct_change(fill_method=None).replace([np.inf, -np.inf], np.nan)

    # Log-return base signals (winsorized later by the feature builder).
    out["ret_1"] = log_ret_1
    return out
