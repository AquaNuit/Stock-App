"""Training pipeline: temporal-split comparison → best-model refit (docs/ml_pipeline.md §1/§5).

Leakage discipline:
- features only ever use data ≤ t (indicator/feature modules guarantee this);
- comparison trains on rows whose targets end strictly before the validation
  window (``split.fit_end``), then predicts *into* the validation window;
- the winner is refit on the full window and calibrated on its newest holdout.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import date

import numpy as np
import pandas as pd

from backend.app.core.constants import HORIZON_DAYS, RANDOM_SEED
from backend.app.core.exceptions import InsufficientHistoryError, TrainingError
from backend.app.core.logging import get_logger
from backend.app.ml.data.preprocessing import clean_ohlcv
from backend.app.ml.evaluation.metrics import regression_metrics
from backend.app.ml.features.engineering import training_view
from backend.app.ml.models.base import BaseForecaster, ModelMetrics
from backend.app.ml.models.registry import ModelRegistry
from backend.app.ml.training.splitter import SplitSpec, make_split

log = get_logger(__name__)


@dataclass(slots=True)
class TrainingResult:
    symbol: str
    data_range: str
    leaderboard: list[ModelMetrics]  # sorted best-first
    best_name: str
    best_model: BaseForecaster  # refit on full window, band-calibrated
    best_metrics: ModelMetrics  # phase-A validation metrics of the winner
    feature_list: list[str]
    context_row: pd.Series
    last_close: float
    last_date: date
    train_rows: int
    val_rows: int
    # filled by PredictionService after persistence:
    training_run_id: int = 0
    model_version: str = ""


class TrainingPipeline:
    def __init__(self, registry: ModelRegistry | None = None, horizon: int = HORIZON_DAYS):
        self.registry = registry or ModelRegistry()
        self.horizon = horizon

    # ------------------------------------------------------------------ public
    def run(
        self,
        frame: pd.DataFrame,
        *,
        symbol: str,
        data_range: str,
        candidate_names: list[str] | None = None,
    ) -> TrainingResult:
        np.random.seed(RANDOM_SEED)
        cleaned = clean_ohlcv(frame)
        features, feature_cols = training_view(cleaned)
        if len(features) < 80:
            raise InsufficientHistoryError(
                f"{symbol}: only {len(features)} complete feature rows after warm-up (need ≥80)"
            )
        split = make_split(len(features))
        # Positionally aligned with `features` (post warm-up dropna/reset_index).
        close = features["close"].astype("float64").reset_index(drop=True)

        names = candidate_names or self.registry.default_candidates()
        names = [n for n in names if self.registry.is_available(n)]
        if not names:
            raise TrainingError("no forecasting models available in this environment")

        leaderboard = [self._evaluate(name, features, feature_cols, close, split) for name in names]
        leaderboard.append(self._naive_benchmark(features, close, split))
        leaderboard.sort(key=lambda m: (np.inf if np.isnan(m.rmse) else m.rmse,
                                        np.inf if np.isnan(m.mape) else m.mape,
                                        np.inf if np.isnan(m.mae) else m.mae))
        for rank, m in enumerate(leaderboard, start=1):
            log.info("rank %d %-15s rmse=%.4f mape=%s r2=%s (%ss)%s",
                     rank, m.name, m.rmse if not np.isnan(m.rmse) else float("nan"),
                     f"{m.mape:.2f}" if not np.isnan(m.mape) else "-",
                     f"{m.r2:.3f}" if not np.isnan(m.r2) else "-",
                     round(m.train_s, 2), " [benchmark]" if m.is_benchmark else "")

        best = next(m for m in leaderboard if not m.is_benchmark)
        if best.error or np.isnan(best.rmse):
            raise TrainingError(f"all candidate models failed: {[m.error for m in leaderboard]}")
        best_name = best.name

        winner = self.registry.create(best_name)
        t0 = time.perf_counter()
        winner.fit(features, feature_cols, close)
        log.info("winner %s refit on full window in %.2fs", best_name, time.perf_counter() - t0)

        return TrainingResult(
            symbol=symbol,
            data_range=data_range,
            leaderboard=leaderboard,
            best_name=best_name,
            best_model=winner,
            best_metrics=best,
            feature_list=list(feature_cols),
            context_row=features.iloc[-1],
            last_close=float(close.iloc[-1]),
            last_date=pd.to_datetime(features["date"].iloc[-1]).date(),
            train_rows=split.fit_end,
            val_rows=split.n_val,
        )

    # ----------------------------------------------------------------- internal
    def _evaluate(
        self,
        name: str,
        features: pd.DataFrame,
        feature_cols: list[str],
        close: pd.Series,
        split: SplitSpec,
    ) -> ModelMetrics:
        t0 = time.perf_counter()
        try:
            model = self.registry.create(name)
            if model.kind == "tabular":
                model.fit(features.iloc[: split.fit_end].reset_index(drop=True), feature_cols, close)
                yt, yp = self._tabular_validation(model, features, split)
            else:
                model.fit(
                    features.iloc[: split.first_val_target].reset_index(drop=True),
                    feature_cols,
                    close.iloc[: split.first_val_target].reset_index(drop=True),
                )
                yp_arr = np.asarray(
                    model._point_forecast(features.iloc[split.first_val_target - 1], split.n_val),
                    dtype="float64",
                )
                yt = close.iloc[split.first_val_target :].to_numpy(dtype="float64")[: len(yp_arr)]
                yp = yp_arr[: len(yt)]
            metrics = regression_metrics(yt, yp)
            return ModelMetrics(
                name=name,
                rmse=metrics["rmse"],
                mae=metrics["mae"],
                mape=metrics["mape"],
                r2=metrics["r2"],
                train_s=time.perf_counter() - t0,
                n_train=split.fit_end,
                n_val=len(yt),
                params=getattr(model, "params", {}),
            )
        except Exception as exc:  # noqa: BLE001 — a broken candidate must not sink the run
            log.warning("model %s failed during comparison: %s", name, exc)
            return ModelMetrics(
                name=name, rmse=float("nan"), mae=float("nan"), mape=float("nan"), r2=float("nan"),
                train_s=time.perf_counter() - t0, n_train=0, n_val=0, error=str(exc)[:300],
            )

    def _tabular_validation(
        self, model: BaseForecaster, features: pd.DataFrame, split: SplitSpec
    ) -> tuple[np.ndarray, np.ndarray]:
        """Per-horizon validation with one vectorized predict (no per-row Python loop).

        Rows t predict targets t+h; only pairs whose target lands inside the
        validation window are scored (leakage-free by construction of fit_end).
        """
        lo = split.first_val_target - self.horizon
        rows = features.iloc[lo : split.n - 1]
        predict_batch = getattr(model, "predict_batch", None)
        if predict_batch is None:
            raise TrainingError(f"tabular model {model.name} lacks predict_batch")
        block_ret = np.asarray(predict_batch(rows, self.horizon), dtype="float64")  # log-returns
        row_close = rows["close"].to_numpy(dtype="float64")
        y_true: list[float] = []
        y_pred: list[float] = []
        ts = range(lo, split.n - 1)
        for h in range(1, self.horizon + 1):
            for i, t in enumerate(ts):
                target_idx = t + h
                if target_idx < split.first_val_target or target_idx > split.n - 1:
                    continue
                y_pred.append(float(row_close[i] * np.exp(block_ret[i, h - 1])))
                y_true.append(float(row_close[i] * np.exp(rows[f"y_h{h}"].iloc[i])))
        return np.asarray(y_true), np.asarray(y_pred)

    def _naive_benchmark(
        self, features: pd.DataFrame, close: pd.Series, split: SplitSpec
    ) -> ModelMetrics:
        """Persistence baseline (close_{t+h} := close_t) — honest context for R²/RMSE."""
        y_true: list[float] = []
        y_pred: list[float] = []
        for h in range(1, self.horizon + 1):
            for t in range(split.first_val_target - h, split.n - h):
                target_idx = t + h
                if target_idx < split.first_val_target or target_idx > split.n - 1:
                    continue
                y_pred.append(float(close.iloc[t]))
                y_true.append(float(close.iloc[target_idx]))
        metrics = regression_metrics(np.asarray(y_true), np.asarray(y_pred))
        return ModelMetrics(
            name="naive_baseline",
            rmse=metrics["rmse"], mae=metrics["mae"], mape=metrics["mape"], r2=metrics["r2"],
            train_s=0.0, n_train=0, n_val=len(y_true), is_benchmark=True,
        )
