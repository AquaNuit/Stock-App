"""Feature matrix assembly: indicators + lags + rolling stats + calendar (docs/ml_pipeline.md §3)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from backend.app.ml.features.technical_indicators import add_technical_indicators

LAG_DAYS = (1, 2, 3, 5, 10, 21)
ROLL_WINDOWS = (5, 10, 21)

BASE_FEATURES = [
    "close_over_sma_5", "close_over_sma_10", "close_over_sma_20", "close_over_sma_50",
    "close_over_sma_100", "close_over_sma_200", "ema_cross_12_26",
    "rsi_14", "macd_hist", "roc_5", "roc_10", "roc_21",
    "atr_pct", "bb_width", "bb_pct_b", "vol_10", "vol_21",
    "close_over_vwap", "obv_slope_10", "vol_change_1",
]

TARGET_HORIZONS = tuple(range(1, 8))  # h=1..7 direct multi-horizon targets


def build_feature_matrix(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Return ``(feature_frame, feature_columns)`` aligned to ``df`` rows.

    Rows in the warm-up region contain NaNs — callers drop them. Also builds
    direct multi-horizon targets ``y_h{1..7} = close shifted by -h``.
    """
    out = add_technical_indicators(df)
    close = out["close"]
    ret1 = out["ret_1"]

    for lag in LAG_DAYS:
        out[f"ret_lag_{lag}"] = ret1.shift(lag)
        out[f"close_lag_{lag}"] = close.shift(lag) / close

    for w in ROLL_WINDOWS:
        mp = max(3, w // 2)
        out[f"ret_mean_{w}"] = ret1.rolling(w, min_periods=mp).mean()
        out[f"ret_std_{w}"] = ret1.rolling(w, min_periods=mp).std()
        out[f"ret_max_{w}"] = ret1.rolling(w, min_periods=mp).max()
        out[f"ret_min_{w}"] = ret1.rolling(w, min_periods=mp).min()

    dates = pd.to_datetime(out["date"])
    dow = dates.dt.dayofweek
    out["dow_sin"] = np.sin(2 * np.pi * dow / 5)
    out["dow_cos"] = np.cos(2 * np.pi * dow / 5)
    out["month_sin"] = np.sin(2 * np.pi * (dates.dt.month - 1) / 12)
    out["month_cos"] = np.cos(2 * np.pi * (dates.dt.month - 1) / 12)
    out["dom_scaled"] = (dates.dt.day - 15) / 15

    # Winsorize return-style features for stability (docs/ml_pipeline.md §2).
    for col in [c for c in out.columns if c.startswith(("ret_", "roc_", "vol_change"))]:
        lo, hi = out[col].quantile(0.01), out[col].quantile(0.99)
        out[col] = out[col].clip(lo, hi)

    # Direct multi-horizon targets are LOG RETURNS, not levels: every feature is
    # stationary/scale-invariant, so a level target would be unlearnable beyond
    # the training window's price range. Price space is reconstructed as
    # close_{t+h} = close_t * exp(y_h) by the forecasters/pipeline.
    for h in TARGET_HORIZONS:
        out[f"y_h{h}"] = np.log(close.shift(-h) / close)

    feature_cols = [c for c in BASE_FEATURES if c in out.columns]
    feature_cols += [f"ret_lag_{l}" for l in LAG_DAYS]
    feature_cols += [f"close_lag_{l}" for l in LAG_DAYS]
    for w in ROLL_WINDOWS:
        feature_cols += [f"ret_mean_{w}", f"ret_std_{w}", f"ret_max_{w}", f"ret_min_{w}"]
    feature_cols += ["dow_sin", "dow_cos", "month_sin", "month_cos", "dom_scaled"]
    return out, feature_cols


def training_view(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Feature matrix restricted to fully-formed rows (no feature NaNs)."""
    enriched, feature_cols = build_feature_matrix(df)
    complete = enriched.dropna(subset=feature_cols).reset_index(drop=True)
    return complete, feature_cols
