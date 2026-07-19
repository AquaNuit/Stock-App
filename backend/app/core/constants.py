"""Domain constants shared across layers (see docs/ml_pipeline.md & docs/api_reference.md)."""

from __future__ import annotations

import math
import re
from enum import StrEnum

API_V1_PREFIX = "/api/v1"

# Forecast horizon: next 7 trading days (project brief).
HORIZON_DAYS = 7

# NSE-ish ticker validation (e.g. RELIANCE, M&M, BAJAJ-AUTO, TATAMOTORS, HDFCLIFE).
SYMBOL_PATTERN = re.compile(r"^[A-Z0-9&\-]{1,20}$")

# Fixed global seed for reproducible pipelines (docs/ml_pipeline.md §8).
RANDOM_SEED = 42

TRADING_DAYS_PER_YEAR = 252
MIN_TRAIN_SESSIONS = 120  # docs/ml_pipeline.md §2


class TimeRange(StrEnum):
    """Historical window selectors exposed to the UI and training."""

    ONE_MONTH = "1m"
    THREE_MONTHS = "3m"
    SIX_MONTHS = "6m"
    ONE_YEAR = "1y"
    TWO_YEARS = "2y"
    FIVE_YEARS = "5y"
    MAX = "max"

    @property
    def calendar_days(self) -> int | None:
        """Approximate calendar-day span (None = unbounded/'max')."""
        return {
            TimeRange.ONE_MONTH: 31,
            TimeRange.THREE_MONTHS: 92,
            TimeRange.SIX_MONTHS: 183,
            TimeRange.ONE_YEAR: 366,
            TimeRange.TWO_YEARS: 731,
            TimeRange.FIVE_YEARS: 1826,
            TimeRange.MAX: None,
        }[self]


ALL_RANGES = [r.value for r in TimeRange]

# Confidence-label thresholds on relative interval half-width (docs/ml_pipeline.md §6).
CONFIDENCE_HIGH_MAX = 0.02
CONFIDENCE_MEDIUM_MAX = 0.05


class Confidence(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ModelName(StrEnum):
    LINEAR = "linear"
    RANDOM_FOREST = "random_forest"
    XGBOOST = "xgboost"
    LIGHTGBM = "lightgbm"
    ARIMA = "arima"
    PROPHET = "prophet"
    LSTM = "lstm"


class DataSource(StrEnum):
    NSE = "nse"
    YFINANCE = "yfinance"
    SEED = "seed"
    CACHE = "cache"
    DB = "db"


def confidence_from_half_width(half_width: float, price: float) -> Confidence:
    """Map relative interval half-width to a display label (docs/ml_pipeline.md §6)."""
    if price <= 0 or not math.isfinite(half_width):
        return Confidence.LOW
    rel = half_width / price
    if rel < CONFIDENCE_HIGH_MAX:
        return Confidence.HIGH
    if rel < CONFIDENCE_MEDIUM_MAX:
        return Confidence.MEDIUM
    return Confidence.LOW
