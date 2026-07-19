"""OHLCV cleaning rules (docs/ml_pipeline.md §2)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from backend.app.core.constants import MIN_TRAIN_SESSIONS
from backend.app.core.exceptions import InsufficientHistoryError

REQUIRED = ["date", "open", "high", "low", "close", "volume"]


def clean_ohlcv(frame: pd.DataFrame, *, min_sessions: int = MIN_TRAIN_SESSIONS) -> pd.DataFrame:
    """Sort/dedupe, coerce dtypes, ffill small gaps, enforce OHLC sanity.

    Returns a frame indexed by ascending ``date`` with columns
    [date, open, high, low, close, adj_close, volume].
    """
    if frame is None or frame.empty:
        raise InsufficientHistoryError("no price history available")

    df = frame.copy()
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise InsufficientHistoryError(f"history missing columns: {missing}")
    if "adj_close" not in df.columns:
        df["adj_close"] = df["close"]

    df["date"] = pd.to_datetime(df["date"]).dt.date
    df = df.drop_duplicates(subset="date", keep="last").sort_values("date").reset_index(drop=True)

    for col in ["open", "high", "low", "close", "adj_close"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["volume"] = pd.to_numeric(df["volume"], errors="coerce").fillna(0).clip(lower=0)

    # Short-gap repair (holidays/vendor gaps), then drop what remains missing.
    df[["open", "high", "low", "close", "adj_close"]] = (
        df[["open", "high", "low", "close", "adj_close"]].ffill(limit=2)
    )
    df = df.dropna(subset=["open", "high", "low", "close"]).reset_index(drop=True)

    # OHLC invariant repair (bad vendor ticks).
    high = df[["open", "high", "low", "close"]].max(axis=1)
    low = df[["open", "high", "low", "close"]].min(axis=1)
    df["high"] = np.maximum(df["high"], high)
    df["low"] = np.minimum(df["low"], low)
    df = df[df["close"] > 0].reset_index(drop=True)
    df["adj_close"] = df["adj_close"].fillna(df["close"])
    df["volume"] = df["volume"].astype("int64")

    if len(df) < min_sessions:
        raise InsufficientHistoryError(
            f"only {len(df)} clean sessions (need ≥{min_sessions}) — widen the range",
        )
    return df
