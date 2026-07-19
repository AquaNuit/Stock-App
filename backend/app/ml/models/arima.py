"""ARIMA wrapper (native recursive strategy; statsmodels backend).

Order is fixed at (2,1,2) for latency; seasonal/Optuna selection is roadmap R2.8
(KI-002). Falls back gracefully via the model registry when statsmodels is absent.
"""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

from backend.app.ml.models.base import BaseForecaster


class ARIMAForecaster(BaseForecaster):
    kind = "series"

    def __init__(self, horizon: int = 7, order: tuple[int, int, int] = (2, 1, 2)):
        super().__init__(horizon, params={"order": order})
        self.name = "arima"
        self.order = order
        self._fit_result = None
        self._context_close: float = 0.0

    def fit(self, features: pd.DataFrame, feature_cols: list[str], close: pd.Series) -> None:  # noqa: ARG002
        from statsmodels.tsa.arima.model import ARIMA

        values = close.to_numpy(dtype="float64")
        model = ARIMA(values, order=self.order, enforce_stationarity=False, enforce_invertibility=False)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self._fit_result = model.fit()
        self._context_close = float(values[-1])

        # Calibrate bands from one-step-ahead in-sample residuals, widened by √h.
        resid = np.asarray(self._fit_result.resid, dtype="float64")
        resid = resid[np.isfinite(resid)]
        if resid.size >= 16:
            base_lo, base_hi = np.quantile(resid, 0.05), np.quantile(resid, 0.95)
            scale = np.sqrt(np.arange(1, self.horizon + 1))
            mean_price = max(float(np.mean(values[-60:])), 1.0)
            self._band_lo = base_lo * scale * (mean_price / mean_price)
            self._band_hi = base_hi * scale

    def _point_forecast(self, context_row: pd.Series, steps: int) -> np.ndarray:  # noqa: ARG002
        assert self._fit_result is not None, "model not fit"
        fc = self._fit_result.get_forecast(steps=steps)
        mean = np.asarray(fc.predicted_mean, dtype="float64")
        try:
            ci = fc.conf_int(alpha=0.10)  # native 5–95% band when available
            ci_arr = np.asarray(ci, dtype="float64")
            self._band_lo = ci_arr[:, 0] - mean
            self._band_hi = ci_arr[:, 1] - mean
        except Exception:  # noqa: BLE001
            pass
        return mean
