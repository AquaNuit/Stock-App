"""Training + 7-day forecast endpoints."""

from __future__ import annotations

import time
from datetime import UTC, datetime

from fastapi import APIRouter, Query

from backend.app.api.deps import PredictionServiceDep
from backend.app.schemas.predictions import (
    ForecastResponse,
    LeaderboardRow,
    ModelRow,
    PredictRequest,
    PredictionHistoryRow,
    TrainRequest,
    TrainResponse,
)

router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.post("/train", response_model=TrainResponse)
def train(body: TrainRequest, svc: PredictionServiceDep) -> TrainResponse:
    t0 = time.perf_counter()
    result = svc.train(body.symbol, body.range, body.models)
    leaderboard = [LeaderboardRow(**m.as_leaderboard_row(i + 1)) for i, m in enumerate(result.leaderboard)]
    best = result.leaderboard[0]
    naive = next((m for m in result.leaderboard if m.is_benchmark), None)
    note = f"{result.best_name} selected (lowest validation RMSE.)"
    if naive and best.rmse and naive.rmse and best.rmse < naive.rmse:
        note = f"{result.best_name} beats the naive-persistence benchmark by {100 * (1 - best.rmse / naive.rmse):.1f}% RMSE."
    return TrainResponse(
        symbol=result.symbol,
        range=result.data_range,
        training_run_id=result.training_run_id,
        best_model=result.best_name,
        best_rmse=result.best_metrics.rmse,
        leadership_note=note,
        leaderboard=leaderboard,
        duration_s=round(time.perf_counter() - t0, 2),
    )


@router.post("/{symbol}", response_model=ForecastResponse)
def predict(symbol: str, body: PredictRequest, svc: PredictionServiceDep) -> ForecastResponse:
    return svc.forecast7(symbol, body.range, force_retrain=body.force_retrain)


@router.get("/{symbol}", response_model=ForecastResponse)
def latest(
    symbol: str,
    svc: PredictionServiceDep,
    range: str = Query(default="2y", pattern="^(1y|2y|5y|max)$"),
) -> ForecastResponse:
    stored = svc.forecast7(symbol, range, force_retrain=False)
    stored.generated_at = stored.generated_at or datetime.now(UTC)
    return stored


@router.get("/{symbol}/history", response_model=dict)
def prediction_history(
    symbol: str,
    svc: PredictionServiceDep,
    limit: int = Query(default=10, ge=1, le=60),
) -> dict:
    rows, realized_mape = svc.history(symbol, limit=limit)
    return {
        "items": [r.model_dump(mode="json") for r in rows],
        "count": len(rows),
        "realized_abs_pct_error_mean": realized_mape,
    }


@router.get("/models/{symbol}", response_model=dict)
def models(symbol: str, svc: PredictionServiceDep) -> dict:
    rows: list[ModelRow] = svc.model_versions(symbol)
    return {"items": [r.model_dump(mode="json") for r in rows], "count": len(rows)}
