"""Direct multi-horizon tabular forecasters (ADR-0009).

One estimator per horizon ``h``: learns ``close_{t+h} = f(X_t)``. At inference
all horizons are queried at the **same** last-known feature row — no recursive
error compounding and per-horizon calibration.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from backend.app.core.constants import RANDOM_SEED
from backend.app.ml.models.base import BaseForecaster

TARGETS = [f"y_h{h}" for h in range(1, 8)]


class DirectForecaster(BaseForecaster):
    kind = "tabular"

    def __init__(self, name: str, factory: Callable[[], object], horizon: int = 7, params: dict | None = None):
        super().__init__(horizon, params)
        self.name = name
        self._factory = factory
        self._estimators: list = []
        self._feature_cols: list[str] = []
        self._context: pd.Series | None = None

    # -- training ---------------------------------------------------------------
    def _xy(self, features: pd.DataFrame, rows: slice | np.ndarray, h: int) -> tuple[np.ndarray, np.ndarray]:
        sub = features.iloc[rows]
        mask = sub[TARGETS[h]].notna().to_numpy()
        X = sub[self._feature_cols].to_numpy(dtype="float32")[mask]
        y = sub[TARGETS[h]].to_numpy(dtype="float64")[mask]
        return X, y

    def fit(self, features: pd.DataFrame, feature_cols: list[str], close: pd.Series) -> None:
        self._feature_cols = feature_cols
        n = len(features)
        self._estimators = []
        y_true_by_h: list[np.ndarray] = []
        y_pred_by_h: list[np.ndarray] = []
        close_arr = features["close"].to_numpy(dtype="float64")
        for h in range(self.horizon):
            est = self._factory()
            X, y = self._xy(features, slice(0, n), h)
            if len(y) < 40:
                raise ValueError(f"insufficient rows ({len(y)}) for horizon {h + 1}")
            est.fit(X, y)
            self._estimators.append(est)
            # Price-space residual hold-out (last 15% per horizon) for CI bands.
            cut = max(1, int(len(y) * 0.85))
            sel = slice(cut, len(y)) if len(y) - cut >= 8 else slice(-8, len(y))
            # X/y rows correspond to feature rows with non-NaN y_h — rebuild mask.
            sub = features.iloc[slice(0, n)]
            mask = sub[TARGETS[h]].notna().to_numpy()
            row_close = close_arr[mask]
            yp_price = row_close[sel] * np.exp(est.predict(X[sel]))
            yt_price = row_close[sel] * np.exp(y[sel])
            y_true_by_h.append(np.asarray(yt_price))
            y_pred_by_h.append(np.asarray(yp_price))
        self._calibrate_bands(y_true_by_h, y_pred_by_h)
        self._context = features.iloc[-1]

    # -- inference ----------------------------------------------------------------
    def _point_forecast(self, context_row: pd.Series, steps: int) -> np.ndarray:  # noqa: ARG002
        """Predicted PRICES: close_t × exp(predicted log-return)."""
        X = np.asarray(context_row[self._feature_cols], dtype="float32").reshape(1, -1)
        base = float(context_row["close"])
        raw = np.array([self._estimators[h].predict(X)[0] for h in range(steps)], dtype="float64")
        return base * np.exp(raw)

    def predict_batch(self, frame: pd.DataFrame, steps: int) -> np.ndarray:
        """Vectorized multi-row forecast of log-returns → (n_rows, steps)."""
        X = frame[self._feature_cols].to_numpy(dtype="float32")
        return np.column_stack(
            [self._estimators[h].predict(X) for h in range(steps)]
        ).astype("float64")

    @property
    def context_row(self) -> pd.Series:
        assert self._context is not None, "model not fit"
        return self._context

    def fitted_params(self) -> dict:
        return {"name": self.name, **self.params}


# -- Concrete factories (registry imports lazily) -----------------------------------

def make_linear() -> DirectForecaster:
    return DirectForecaster(
        "linear",
        lambda: Pipeline([("scale", StandardScaler()), ("ridge", Ridge(alpha=3.0))]),
        params={"alpha": 3.0, "family": "ridge", "scaled": True},
    )


def make_random_forest() -> DirectForecaster:
    return DirectForecaster(
        "random_forest",
        lambda: RandomForestRegressor(
            # Seven direct-horizon estimators are fitted per run. A compact,
            # single-worker forest avoids CPU/RAM spikes in 1 GB containers.
            n_estimators=32, max_depth=8, min_samples_leaf=6,
            n_jobs=1, random_state=RANDOM_SEED,
        ),
        params={"n_estimators": 32, "max_depth": 8, "n_jobs": 1},
    )


def make_xgboost() -> DirectForecaster:
    from xgboost import XGBRegressor

    return DirectForecaster(
        "xgboost",
        lambda: XGBRegressor(
            n_estimators=48, learning_rate=0.08, max_depth=4,
            subsample=0.9, colsample_bytree=0.8, reg_lambda=1.0,
            tree_method="hist", n_jobs=1, random_state=RANDOM_SEED,
        ),
        params={"n_estimators": 48, "learning_rate": 0.08, "max_depth": 4, "n_jobs": 1},
    )


def make_lightgbm() -> DirectForecaster:
    from lightgbm import LGBMRegressor

    return DirectForecaster(
        "lightgbm",
        lambda: LGBMRegressor(
            n_estimators=64, learning_rate=0.08, num_leaves=15,
            subsample=0.9, colsample_bytree=0.8, n_jobs=1,
            random_state=RANDOM_SEED, verbose=-1,
        ),
        params={"n_estimators": 64, "learning_rate": 0.08, "num_leaves": 15, "n_jobs": 1},
    )
