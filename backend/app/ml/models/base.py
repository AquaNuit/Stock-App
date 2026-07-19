"""Forecaster contracts (docs/architecture.md §5.2).

Two families behind one interface:
- ``tabular`` (direct multi-horizon): fit on engineered features, one estimator
  per horizon, all queried at the last known row (ADR-0009).
- ``series`` (native recursive): consume the close path directly
  (ARIMA, Prophet, LSTM).
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from datetime import date

import numpy as np
import pandas as pd


@dataclass(slots=True)
class PointForecast:
    """Conformal-banded forecast for the 7 trading days ahead."""

    dates: list[date]
    point: np.ndarray
    lower: np.ndarray
    upper: np.ndarray
    last_close: float


@dataclass(slots=True)
class ModelMetrics:
    name: str
    rmse: float
    mae: float
    mape: float
    r2: float
    train_s: float
    n_train: int
    n_val: int
    params: dict = field(default_factory=dict)
    error: str = ""
    is_benchmark: bool = False  # naive baselines are shown but never selectable

    def as_leaderboard_row(self, rank: int) -> dict:
        return {
            "rank": rank,
            "model": self.name,
            "rmse": round(self.rmse, 4) if pd.notna(self.rmse) else None,
            "mae": round(self.mae, 4) if pd.notna(self.mae) else None,
            "mape": round(self.mape, 4) if pd.notna(self.mape) else None,
            "r2": round(self.r2, 4) if pd.notna(self.r2) else None,
            "train_seconds": round(self.train_s, 3),
            "benchmark": self.is_benchmark,
            "error": self.error or None,
        }


class BaseForecaster(abc.ABC):
    """Fit → forecast(steps) → PointForecast. Fit must store residual bands."""

    name: str = "abstract"
    kind: str = "tabular"  # or "series"

    def __init__(self, horizon: int = 7, params: dict | None = None):
        self.horizon = horizon
        self.params = params or {}
        self._band_lo = np.full(horizon, -0.02)  # residual quantiles (default ±2%)
        self._band_hi = np.full(horizon, 0.02)

    @abc.abstractmethod
    def fit(self, features: pd.DataFrame, feature_cols: list[str], close: pd.Series) -> None:
        """Train on history + calibrate residual bands from in-window residuals."""

    @abc.abstractmethod
    def _point_forecast(self, context_row: pd.Series, steps: int) -> np.ndarray:
        """Point predictions for the next ``steps`` sessions (h=1..steps)."""

    def forecast(self, context_row: pd.Series, last_close: float, future_dates: list[date]) -> PointForecast:
        steps = len(future_dates)
        point = np.asarray(self._point_forecast(context_row, steps), dtype="float64")
        lo = np.asarray(self._band_lo[:steps], dtype="float64")
        hi = np.asarray(self._band_hi[:steps], dtype="float64")
        # Interval floor of ±0.5% to avoid degenerate zero-width bands (docs §6).
        lower = np.minimum(point + lo, point - 0.005 * np.abs(point))
        upper = np.maximum(point + hi, point + 0.005 * np.abs(point))
        return PointForecast(dates=future_dates, point=point, lower=lower, upper=upper, last_close=last_close)

    def _calibrate_bands(self, y_true_by_h: list[np.ndarray], y_pred_by_h: list[np.ndarray]) -> None:
        """Residual-quantile (conformal) bands per horizon."""
        for h, (yt, yp) in enumerate(zip(y_true_by_h, y_pred_by_h, strict=False)):
            if h >= self.horizon:
                break
            resid = np.asarray(yt, dtype="float64") - np.asarray(yp, dtype="float64")
            resid = resid[np.isfinite(resid)]
            if resid.size >= 8:
                self._band_lo[h] = float(np.quantile(resid, 0.05))
                self._band_hi[h] = float(np.quantile(resid, 0.95))


@dataclass(slots=True)
class ForecastBundle:
    """Everything the prediction service needs to serve + persist a forecast."""

    symbol: str
    model_name: str
    version: str
    metrics: ModelMetrics
    forecast: PointForecast
    feature_list: list[str]
    data_range: str
    train_rows: int
    val_rows: int
