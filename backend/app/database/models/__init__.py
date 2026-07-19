"""ORM model registry — imported for side effects before ``create_all``."""

from backend.app.database.models.historical_price import HistoricalPrice
from backend.app.database.models.prediction import Model, Prediction, TrainingRun
from backend.app.database.models.stock import Stock
from backend.app.database.models.user import SearchHistory, User, Watchlist, WatchlistItem

__all__ = [
    "Stock",
    "HistoricalPrice",
    "Prediction",
    "Model",
    "TrainingRun",
    "User",
    "Watchlist",
    "WatchlistItem",
    "SearchHistory",
]
