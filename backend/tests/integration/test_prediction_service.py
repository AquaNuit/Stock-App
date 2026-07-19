"""PredictionService end-to-end on the hermetic chain: train → persist → reuse → versions."""

from __future__ import annotations

from backend.app.ml.models.registry import ModelRegistry
from backend.app.ml.training.pipeline import TrainingPipeline
from backend.app.services.prediction_service import PredictionService
from backend.app.services.stock_service import StockService


def _service(session, chain, settings) -> PredictionService:
    stock_svc = StockService(session, chain)
    pipe = TrainingPipeline(ModelRegistry())
    return PredictionService(session, stock_svc, pipeline=pipe, settings=settings)


def test_train_forecast_persist_and_cached_reuse(session, chain, settings):
    svc = _service(session, chain, settings)
    result = svc.train("WIPRO", "1y", models=["linear", "random_forest"])
    assert result.training_run_id > 0
    assert result.model_version.startswith("v:WIPRO:")
    assert result.leaderboard[0].rmse == min(m.rmse for m in result.leaderboard)

    fc = svc.forecast7("WIPRO", "1y", force_retrain=True)
    assert fc.cached is False
    assert len(fc.forecasts) == 7
    assert fc.model in {"linear", "random_forest"}
    assert all(f.lower_bound <= f.predicted_price <= f.upper_bound for f in fc.forecasts)

    again = svc.forecast7("WIPRO", "1y", force_retrain=False)
    assert again.cached is True  # same-day batch reuse
    assert [d.date for d in again.forecasts] == [d.date for d in fc.forecasts]

    versions = svc.model_versions("WIPRO")
    assert versions and versions[0].status in {"selected", "retired"}


def test_history_rows_and_realized_accuracy(session, chain, settings):
    svc = _service(session, chain, settings)
    svc.forecast7("SBIN", "1y", force_retrain=True)
    rows, mape = svc.history("SBIN", limit=3)
    assert rows and all(r.horizon >= 1 for r in rows)
    # today's batch targets future dates → realized columns empty but keys present
    assert rows[0].realized_close is None
    assert mape is None or mape >= 0


def test_unknown_symbol_raises(session, chain, settings):
    import pytest

    from backend.app.core.exceptions import SymbolNotFoundError

    svc = _service(session, chain, settings)
    with pytest.raises(SymbolNotFoundError):
        svc.train("NOT_A_TICKER", "1y", models=["linear"])

