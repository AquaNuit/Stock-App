"""Turns a fitted winner + training context into the 7-day forecast DTOs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

import numpy as np
import pandas as pd

from backend.app.core.constants import HORIZON_DAYS, Confidence, confidence_from_half_width
from backend.app.ml.training.pipeline import TrainingResult


@dataclass(slots=True)
class DayForecast:
    date: date
    horizon: int
    predicted_price: float
    lower_bound: float
    upper_bound: float
    expected_change: float
    expected_change_pct: float
    confidence: Confidence


def next_business_days(after: date, n: int) -> list[date]:
    days = pd.bdate_range(start=after + timedelta(days=1), periods=n)
    return [d.date() for d in days]


class Forecaster:
    """Builds DayForecast rows from a ``TrainingResult`` (docs/ml_pipeline.md §6)."""

    def __init__(self, result: TrainingResult, horizon: int = HORIZON_DAYS):
        self.result = result
        self.horizon = horizon

    def forecast(self) -> list[DayForecast]:
        dates = next_business_days(self.result.last_date, self.horizon)
        pf = self.result.best_model.forecast(self.result.context_row, self.result.last_close, dates)
        out: list[DayForecast] = []
        for i, day in enumerate(dates):
            price = float(pf.point[i])
            lower, upper = float(pf.lower[i]), float(pf.upper[i])
            change = price - self.result.last_close
            pct = (change / self.result.last_close) * 100 if self.result.last_close else 0.0
            out.append(
                DayForecast(
                    date=day,
                    horizon=i + 1,
                    predicted_price=round(price, 2),
                    lower_bound=round(min(lower, price), 2),
                    upper_bound=round(max(upper, price), 2),
                    expected_change=round(change, 2),
                    expected_change_pct=round(pct, 4),
                    confidence=confidence_from_half_width(max(upper - price, price - lower), price),
                )
            )
        return out


def band_width_pct(forecasts: list[DayForecast]) -> np.ndarray:
    """Relative band widths — used by insights and tests of interval sanity."""
    return np.array([
        (f.upper_bound - f.lower_bound) / f.predicted_price if f.predicted_price else np.nan
        for f in forecasts
    ])
