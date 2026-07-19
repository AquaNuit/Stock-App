"""Core cross-cutting concerns: settings, logging, constants, domain errors."""

from backend.app.core.config import Settings, get_settings
from backend.app.core.constants import (
    HORIZON_DAYS,
    MIN_TRAIN_SESSIONS,
    SYMBOL_PATTERN,
    Confidence,
    DataSource,
    ModelName,
    TimeRange,
)
from backend.app.core.exceptions import (
    DomainError,
    InsufficientHistoryError,
    NoModelAvailableError,
    ProviderUnavailableError,
    SymbolNotFoundError,
    TrainingError,
)
from backend.app.core.logging import configure_logging, get_logger

__all__ = [
    "Settings",
    "get_settings",
    "configure_logging",
    "get_logger",
    "HORIZON_DAYS",
    "MIN_TRAIN_SESSIONS",
    "SYMBOL_PATTERN",
    "Confidence",
    "DataSource",
    "ModelName",
    "TimeRange",
    "DomainError",
    "SymbolNotFoundError",
    "ProviderUnavailableError",
    "InsufficientHistoryError",
    "TrainingError",
    "NoModelAvailableError",
]
