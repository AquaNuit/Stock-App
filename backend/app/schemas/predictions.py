"""Prediction DTOs."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator

from backend.app.core.constants import ALL_RANGES, SYMBOL_PATTERN


class TrainRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=20)
    range: str = Field(default="2y", pattern="^(1y|2y|5y|max)$")
    models: list[str] | None = Field(default=None, description="subset of registry names; default = auto zoo")

    @field_validator("symbol")
    @classmethod
    def _symbol_ok(cls, v: str) -> str:
        v = v.strip().upper()
        if not SYMBOL_PATTERN.match(v):
            raise ValueError("invalid symbol")
        return v


class PredictRequest(BaseModel):
    range: str = Field(default="2y", pattern="^(1y|2y|5y|max)$")
    force_retrain: bool = False


class DayForecastOut(BaseModel):
    date: date
    day: str  # e.g. "Mon 20 Jul"
    horizon: int
    predicted_price: float
    lower_bound: float
    upper_bound: float
    expected_change: float
    expected_change_pct: float
    confidence: str


class LeaderboardRow(BaseModel):
    rank: int
    model: str
    rmse: float | None
    mae: float | None
    mape: float | None
    r2: float | None
    train_seconds: float
    benchmark: bool = False
    error: str | None = None


class TrainResponse(BaseModel):
    symbol: str
    range: str
    training_run_id: int
    best_model: str
    best_rmse: float | None
    leadership_note: str
    leaderboard: list[LeaderboardRow]
    duration_s: float


class ForecastResponse(BaseModel):
    symbol: str
    range: str
    generated_at: datetime
    last_close: float
    last_date: date
    model: str
    model_version: str
    model_rmse: float | None
    training_run_id: int
    cached: bool
    forecasts: list[DayForecastOut]
    leaderboard: list[LeaderboardRow] | None = None


class PredictionHistoryRow(BaseModel):
    prediction_date: date
    target_date: date
    horizon: int
    predicted_price: float
    lower_bound: float
    upper_bound: float
    model_name: str
    realized_close: float | None = None
    abs_pct_error: float | None = None


class ModelRow(BaseModel):
    id: int
    name: str
    version: str
    status: str
    rmse: float | None
    mae: float | None
    mape: float | None
    r2: float | None
    data_range: str
    trained_at: datetime
    train_rows: int
    val_rows: int


__all__ = [
    "TrainRequest", "PredictRequest", "DayForecastOut", "LeaderboardRow",
    "TrainResponse", "ForecastResponse", "PredictionHistoryRow", "ModelRow", "ALL_RANGES",
]
