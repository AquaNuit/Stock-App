"""Data-access layer — the only place SQL lives."""

from backend.app.repositories.models_repo import ModelRepository, TrainingRunRepository
from backend.app.repositories.predictions import PredictionRepository
from backend.app.repositories.prices import PriceRepository
from backend.app.repositories.stocks import StockRepository
from backend.app.repositories.users import SearchRepository, UserRepository, WatchlistRepository

__all__ = [
    "StockRepository",
    "PriceRepository",
    "PredictionRepository",
    "ModelRepository",
    "TrainingRunRepository",
    "UserRepository",
    "WatchlistRepository",
    "SearchRepository",
]
