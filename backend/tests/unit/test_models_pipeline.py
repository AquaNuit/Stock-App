"""Model-zoo behavior: registry guards, learnable signal, band sanity, leaderboard."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from backend.app.ml.features.engineering import training_view
from backend.app.ml.models.registry import ModelRegistry
from backend.app.ml.prediction.forecaster import Forecaster, band_width_pct
from backend.app.ml.training.pipeline import TrainingPipeline
from backend.app.providers.seed_provider import generate_series


def _trending_frame(n: int = 400) -> pd.DataFrame:
    """Nearly-deterministic cyclical trend (63-session cycle) + light noise.

    Momentum/ROC features make next-week direction genuinely learnable, so a
    competent model must beat naive persistence by a clear margin.
    """
    rng = np.random.default_rng(7)
    days = pd.bdate_range("2023-01-02", periods=n)
    t = np.arange(n)
    log_price = np.log(100) + 0.0008 * t + 0.10 * np.sin(2 * np.pi * t / 63)
    close = np.exp(log_price) * (1 + rng.normal(0, 0.002, n))
    open_ = np.roll(close, 1)
    open_[0] = close[0]
    high = np.maximum(open_, close) * 1.002
    low = np.minimum(open_, close) * 0.998
    vol = rng.integers(100_000, 900_000, n)
    return pd.DataFrame(
        {"date": days.date, "open": open_, "high": high, "low": low,
         "close": close, "adj_close": close, "volume": vol}
    )


def test_registry_guards_optional_models():
    reg = ModelRegistry()
    names = reg.available()
    assert {"linear", "random_forest"} <= set(names)  # sklearn always present
    # default candidates must all be creatable
    for name in reg.default_candidates():
        model = reg.create(name)
        assert model.name == name
    with pytest.raises(KeyError):
        reg.create("does_not_exist")


def test_model_zoo_beats_naive_on_cyclical_signal():
    frame = _trending_frame()
    pipe = TrainingPipeline(ModelRegistry())
    result = pipe.run(frame, symbol="TEST", data_range="2y", candidate_names=["linear", "random_forest"])
    naive = next(m for m in result.leaderboard if m.is_benchmark)
    best = result.leaderboard[0]
    assert not best.is_benchmark
    assert best.rmse < 0.95 * naive.rmse  # clear margin on learnable cyclical signal
    assert result.best_name == best.name


def test_forecast_bands_are_sane_and_ordered():
    frame = generate_series("RELIANCE").tail(400)
    pipe = TrainingPipeline(ModelRegistry())
    result = pipe.run(frame, symbol="RELIANCE", data_range="2y", candidate_names=["linear"])
    days = Forecaster(result).forecast()
    assert len(days) == 7
    for d in days:
        assert d.lower_bound <= d.predicted_price <= d.upper_bound + 1e-9
        assert d.predicted_price > 0
        assert d.date.weekday() < 5  # trading days only
        assert abs(d.expected_change_pct) < 40  # no crazy 7d moves
    widths = band_width_pct(days)
    assert np.all(np.isfinite(widths))
    assert (widths > 0).all()
    assert (widths < 0.60).all()  # 7-day bands shouldn't explode past ±30%


def test_leaderboard_sorted_and_winner_is_not_benchmark():
    """On near-random-walk data the naive benchmark may legitimately rank first —
    the contract is: ranking is honest, and the *selected* model excludes benchmarks."""
    frame = generate_series("TCS").tail(350)
    pipe = TrainingPipeline(ModelRegistry())
    result = pipe.run(frame, symbol="TCS", data_range="1y",
                      candidate_names=["linear", "random_forest"])
    rmses = [m.rmse for m in result.leaderboard]
    assert rmses == sorted(rmses, key=lambda x: (np.inf if np.isnan(x) else x))
    assert any(m.is_benchmark for m in result.leaderboard)
    assert result.best_name != "naive_baseline"
    first_real = next(m for m in result.leaderboard if not m.is_benchmark)
    assert first_real.name == result.best_name


def test_feature_frame_alignment_with_series_targets():
    """Regression guard for the close/features index-alignment bug (found in dev)."""
    frame = generate_series("SBIN").tail(300)
    features, cols = training_view(frame)
    close = features["close"].reset_index(drop=True)
    assert features.index.equals(close.index)
    assert len(features) > 80
