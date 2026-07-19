"""Prophet wrapper — registered only when the optional dependency exists (ADR-0008)."""

from __future__ import annotations

import contextlib
import io

import numpy as np
import pandas as pd

from backend.app.ml.models.base import BaseForecaster


class ProphetForecaster(BaseForecaster):
    kind = "series"

    def __init__(self, horizon: int = 7):
        super().__init__(horizon, params={"seasonality_mode": "multiplicative", "weekly": True})
        self.name = "prophet"
        self._model = None

    def fit(self, features: pd.DataFrame, feature_cols: list[str], close: pd.Series) -> None:  # noqa: ARG002
        from prophet import Prophet

        frame = pd.DataFrame(
            {"ds": pd.to_datetime(features["date"]), "y": close.to_numpy(dtype="float64")}
        )
        model = Prophet(
            daily_seasonality=False,
            weekly_seasonality=True,
            yearly_seasonality=True,
            seasonality_mode="multiplicative",
            interval_width=0.90,
        )
        with contextlib.redirect_stdout(io.StringIO()):  # mute cmdstan chatter
            model.fit(frame)
        self._model = model

    def _point_forecast(self, context_row: pd.Series, steps: int) -> np.ndarray:  # noqa: ARG002
        assert self._model is not None, "model not fit"
        future = self._model.make_future_dataframe(periods=steps, freq="B", include_history=False)
        fc = self._model.predict(future).tail(steps)
        mean = fc["yhat"].to_numpy(dtype="float64")
        self._band_lo = fc["yhat_lower"].to_numpy(dtype="float64") - mean
        self._band_hi = fc["yhat_upper"].to_numpy(dtype="float64") - mean
        return mean
