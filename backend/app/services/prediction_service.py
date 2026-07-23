"""Prediction use-cases: train → version → persist → serve 7-day forecasts (docs/architecture.md §7)."""

from __future__ import annotations

import threading
import time
from datetime import UTC, date, datetime

from sqlalchemy.orm import Session

from backend.app.core.config import Settings, get_settings
from backend.app.core.constants import TimeRange
from backend.app.core.exceptions import NoModelAvailableError, TrainingError
from backend.app.core.logging import get_logger
from backend.app.database.models import Model, Prediction
from backend.app.ml.models.base import ModelMetrics
from backend.app.ml.prediction.forecaster import DayForecast, Forecaster
from backend.app.ml.training.pipeline import TrainingPipeline, TrainingResult
from backend.app.repositories import (
    ModelRepository,
    PredictionRepository,
    PriceRepository,
    StockRepository,
    TrainingRunRepository,
)
from backend.app.schemas.predictions import (
    DayForecastOut,
    ForecastResponse,
    LeaderboardRow,
    ModelRow,
    PredictionHistoryRow,
)
from backend.app.services.stock_service import StockService

log = get_logger(__name__)

# Global train concurrency guard (docs/deployment.md §6).
_TRAIN_SEMAPHORE: threading.Semaphore | None = None


def _semaphore(settings: Settings) -> threading.Semaphore:
    global _TRAIN_SEMAPHORE
    if _TRAIN_SEMAPHORE is None:
        _TRAIN_SEMAPHORE = threading.Semaphore(settings.max_concurrent_trains)
    return _TRAIN_SEMAPHORE


def _version(symbol: str, model_name: str) -> str:
    return f"v:{symbol}:{model_name}:{datetime.now(UTC).isoformat(timespec='seconds')}"


def _day_label(d: date) -> str:
    """Portable ``"Mon 20 Jul"`` label.

    ``strftime("%-d")`` is a glibc-only extension — it raises
    ``ValueError: Invalid format string`` on Windows, taking down every
    forecast response. Compose the label from portable pieces instead.
    """
    return f"{d:%a} {d.day} {d:%b}"


class PredictionService:
    def __init__(
        self,
        session: Session,
        stock_service: StockService,
        pipeline: TrainingPipeline | None = None,
        settings: Settings | None = None,
    ):
        self.session = session
        self.stock_service = stock_service
        self.settings = settings or get_settings()
        self.pipeline = pipeline or TrainingPipeline(settings=self.settings)
        self.models = ModelRepository(session)
        self.runs = TrainingRunRepository(session)
        self.predictions = PredictionRepository(session)
        self.stocks = StockRepository(session)
        self.prices = PriceRepository(session)

    # ---------------------------------------------------------------- train
    def train(self, symbol: str, range_value: str = "2y", models: list[str] | None = None) -> TrainingResult:
        tr = TimeRange(range_value)
        if tr.calendar_days and tr.calendar_days > self.settings.train_max_range_years * 366:
            raise TrainingError(f"range {tr.value} exceeds TRAIN_MAX_RANGE_YEARS")
        sem = _semaphore(self.settings)
        if not sem.acquire(blocking=False):
            raise TrainingError("training capacity busy — retry shortly", code="TRAIN_BUSY")
        try:
            frame, _source = self.stock_service.get_history_frame(symbol, tr)
            result = self.pipeline.run(frame, symbol=symbol.upper(), data_range=tr.value, candidate_names=models)
            self._persist_training(result)
            return result
        finally:
            sem.release()

    def _persist_training(self, result: TrainingResult) -> None:
        stock = self.stocks.by_symbol(result.symbol)
        assert stock is not None, "stock must exist after get_history_frame"
        run = self.runs.create_run(
            stock_id=stock.id, trigger_type="manual", data_range=result.data_range,
        )
        leaderboard_rows = [m.as_leaderboard_row(i + 1) for i, m in enumerate(result.leaderboard)]
        version = _version(result.symbol, result.best_name)
        try:
            best_metrics: ModelMetrics = result.best_metrics
            model_row = Model(
                name=result.best_name,
                version=version,
                stock_id=stock.id,
                status="selected",
                hyperparams=result.best_model.params,
                feature_list=result.feature_list,
                rmse=best_metrics.rmse, mae=best_metrics.mae,
                mape=best_metrics.mape, r2=best_metrics.r2,
                data_range=result.data_range,
                train_rows=result.train_rows, val_rows=result.val_rows,
            )
            # Retire previous "selected" rows for this symbol.
            for old in self.models.for_symbol(stock.id, limit=100):
                if old.status == "selected":
                    old.status = "retired"
            self.models.add(model_row)
            run.model_id = model_row.id
            run.status = "success"
            run.leaderboard = leaderboard_rows
            run.best_model = result.best_name
            run.best_rmse = best_metrics.rmse
            run.finished_at = datetime.now(UTC)
            self.session.commit()
            result.training_run_id = int(run.id)
            result.model_version = version
        except Exception:
            run.status = "failed"
            run.finished_at = datetime.now(UTC)
            self.session.commit()
            raise

    # ---------------------------------------------------------------- forecast
    def forecast7(self, symbol: str, range_value: str = "2y", *, force_retrain: bool = False) -> ForecastResponse:
        symbol = symbol.upper()
        stock = self.stock_service._require_stock(symbol)

        if not force_retrain:
            stored = self._stored_today(stock.id, range_value)
            if stored is not None:
                return stored

        t0 = time.perf_counter()
        result = self.train(symbol, range_value)
        days = Forecaster(result).forecast()
        self._persist_predictions(result, days)
        leaderboard = [LeaderboardRow(**m.as_leaderboard_row(i + 1)) for i, m in enumerate(result.leaderboard)]
        log.info("forecast for %s served in %.2fs (model=%s)", symbol, time.perf_counter() - t0, result.best_name)
        return ForecastResponse(
            symbol=symbol,
            range=result.data_range,
            generated_at=datetime.now(UTC),
            last_close=result.last_close,
            last_date=result.last_date,
            model=result.best_name,
            model_version=result.model_version,
            model_rmse=self._clean_nan(result.best_metrics.rmse),
            training_run_id=result.training_run_id,
            cached=False,
            forecasts=[self._day_out(d) for d in days],
            leaderboard=leaderboard,
        )

    def _day_out(self, d: DayForecast) -> DayForecastOut:
        return DayForecastOut(
            date=d.date,
            day=_day_label(d.date),
            horizon=d.horizon,
            predicted_price=d.predicted_price,
            lower_bound=d.lower_bound,
            upper_bound=d.upper_bound,
            expected_change=d.expected_change,
            expected_change_pct=d.expected_change_pct,
            confidence=d.confidence.value,
        )

    def _persist_predictions(self, result: TrainingResult, days: list[DayForecast]) -> None:
        stock = self.stocks.by_symbol(result.symbol)
        assert stock is not None
        rows = [
            Prediction(
                stock_id=stock.id,
                training_run_id=result.training_run_id or None,
                prediction_date=date.today(),
                target_date=d.date,
                horizon=d.horizon,
                predicted_price=d.predicted_price,
                lower_bound=d.lower_bound,
                upper_bound=d.upper_bound,
                expected_change_pct=d.expected_change_pct,
                confidence=d.confidence.value,
                model_name=result.best_name,
                model_version=result.model_version,
                model_rmse=result.best_metrics.rmse,
                range_used=result.data_range,
            )
            for d in days
        ]
        self.predictions.save_batch(rows)
        self.session.commit()

    def _stored_today(self, stock_id: int, range_value: str) -> ForecastResponse | None:
        batch = self.predictions.latest_batch(stock_id)
        today = date.today()
        fresh = [p for p in batch if p.prediction_date >= today and p.range_used == range_value]
        if len(fresh) < 7:
            return None
        stock = self.stocks.get(stock_id)
        assert stock is not None
        fresh.sort(key=lambda p: p.horizon)
        last_close = self.prices.to_frame(stock_id)["close"].iloc[-1] if self.prices.count_for(stock_id) else None
        model_name = fresh[0].model_name
        days = [
            DayForecastOut(
                date=p.target_date,
                day=_day_label(p.target_date),
                horizon=p.horizon,
                predicted_price=round(p.predicted_price, 2),
                lower_bound=round(p.lower_bound, 2),
                upper_bound=round(p.upper_bound, 2),
                expected_change=round(
                    p.predicted_price - (float(last_close) if last_close is not None else p.predicted_price), 2
                ),
                expected_change_pct=round(p.expected_change_pct, 4),
                confidence=p.confidence,
            )
            for p in fresh[:7]
        ]
        return ForecastResponse(
            symbol=stock.symbol,
            range=range_value,
            generated_at=datetime.now(UTC),
            last_close=float(last_close) if last_close is not None else 0.0,
            last_date=today,
            model=model_name,
            model_version=fresh[0].model_version,
            model_rmse=self._clean_nan(fresh[0].model_rmse),
            training_run_id=int(fresh[0].training_run_id or 0),
            cached=True,
            forecasts=days,
            leaderboard=None,
        )

    # ---------------------------------------------------------------- history/models
    def history(self, symbol: str, *, limit: int = 10) -> tuple[list[PredictionHistoryRow], float | None]:
        stock = self.stock_service._require_stock(symbol)
        rows = self.predictions.history(stock.id, limit=limit)
        frame = self.prices.to_frame(stock.id)
        realized = {r.date: float(r.close) for r in frame.itertuples(index=False)} if not frame.empty else {}
        out: list[PredictionHistoryRow] = []
        errors: list[float] = []
        for p in rows:
            actual = realized.get(p.target_date)
            ape = None
            if actual is not None and p.target_date <= max(realized.keys(), default=date.min):
                ape = abs(actual - p.predicted_price) / p.predicted_price * 100
                if p.target_date <= date.today():
                    errors.append(ape)
            out.append(
                PredictionHistoryRow(
                    prediction_date=p.prediction_date, target_date=p.target_date,
                    horizon=p.horizon, predicted_price=round(p.predicted_price, 2),
                    lower_bound=round(p.lower_bound, 2), upper_bound=round(p.upper_bound, 2),
                    model_name=p.model_name,
                    realized_close=actual,
                    abs_pct_error=round(ape, 3) if ape is not None else None,
                )
            )
        mape = round(sum(errors) / len(errors), 3) if errors else None
        return out, mape

    def _clean_nan(self, v: float | None) -> float | None:
        if v is None:
            return None
        import math
        if math.isnan(v) or math.isinf(v):
            return None
        return float(v)

    def model_versions(self, symbol: str) -> list[ModelRow]:
        stock = self.stock_service._require_stock(symbol)
        rows = self.models.for_symbol(stock.id)
        return [
            ModelRow(
                id=m.id, name=m.name, version=m.version, status=m.status,
                rmse=self._clean_nan(m.rmse), mae=self._clean_nan(m.mae),
                mape=self._clean_nan(m.mape), r2=self._clean_nan(m.r2),
                data_range=m.data_range, trained_at=m.trained_at,
                train_rows=m.train_rows, val_rows=m.val_rows,
            )
            for m in rows
        ]
