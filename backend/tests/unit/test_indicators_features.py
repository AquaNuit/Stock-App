"""Indicators + feature engineering: columns, no look-ahead, stationary features."""

from __future__ import annotations

import numpy as np
import pandas as pd

from backend.app.ml.features.engineering import build_feature_matrix, training_view
from backend.app.ml.features.technical_indicators import add_technical_indicators
from backend.app.providers.seed_provider import generate_series


def _frame(n: int = 700) -> pd.DataFrame:
    return generate_series("RELIANCE").tail(n).reset_index(drop=True)


def test_indicator_catalog_columns_present():
    e = add_technical_indicators(_frame())
    expected = [
        "sma_20", "sma_50", "sma_200", "ema_12", "ema_26", "rsi_14", "macd",
        "macd_signal", "macd_hist", "atr_14", "atr_pct", "bb_width", "bb_pct_b",
        "vwap_20", "close_over_vwap", "obv", "obv_slope_10", "roc_5", "roc_21",
        "mom_10", "vol_10", "vol_21", "ret_1",
    ]
    for col in expected:
        assert col in e.columns, col


def test_rsi_bounds_and_macd_consistency():
    e = add_technical_indicators(_frame()).dropna(subset=["rsi_14"])
    assert e["rsi_14"].between(0, 100).all()
    hist = (e["macd"] - e["macd_signal"] - e["macd_hist"]).dropna()
    assert (hist.abs() < 1e-8).all()


def test_no_lookahead_invariant():
    """Indicators at row t must not change when the *future* is altered."""
    n = 700
    base = add_technical_indicators(_frame(n))
    altered_df = _frame(n).copy()
    altered_df.loc[altered_df.index[-30:], ["open", "high", "low", "close"]] *= 1.5
    altered_df.loc[altered_df.index[-30:], "volume"] *= 3
    altered = add_technical_indicators(altered_df)
    cols = ["close_over_sma_20", "rsi_14", "macd_hist", "atr_pct", "bb_pct_b", "vol_21"]
    for col in cols:
        a = base[col].iloc[:-30].to_numpy()
        b = altered[col].iloc[:-30].to_numpy()
        same = (np.isnan(a) & np.isnan(b)) | np.isclose(a, b, atol=1e-8, equal_nan=True)
        assert same.all(), f"look-ahead detected in {col}"


def test_feature_matrix_contract():
    frame = _frame()
    enriched, cols = build_feature_matrix(frame)
    assert len(enriched) == len(frame)
    assert len(cols) >= 45  # ~49 engineered features (indicator ratios + lags + rolling + calendar)
    # log-return targets: y_h3 = log(close_{t+3}/close_t)
    i = 50
    expected = np.log(enriched["close"].iloc[i + 3] / enriched["close"].iloc[i])
    assert abs(enriched["y_h3"].iloc[i] - expected) < 1e-9
    train, cols2 = training_view(frame)
    assert cols2 == cols
    assert not train[cols].isna().any().any()
    # all features stationary-ish (ratio bounded, no raw price levels)
    for col in [c for c in cols if c.startswith("close_over_sma")]:
        assert train[col].between(0.1, 10).all()


def test_winsorization_bounds_outliers():
    train, cols = training_view(_frame())
    for col in [c for c in cols if c.startswith("ret_lag")]:
        assert train[col].abs().max() < 0.5  # daily log returns winsorized ≤ ~50%
