"""Model registry with graceful optional-dependency guards (ADR-0008).

Availability is probed once at import; ``available()`` only ever returns models
that can actually train in the current environment.
"""

from __future__ import annotations

import importlib.util
from typing import Callable

from backend.app.core.logging import get_logger
from backend.app.ml.models.base import BaseForecaster
from backend.app.ml.models.direct import make_linear, make_lightgbm, make_random_forest, make_xgboost

log = get_logger(__name__)

Factory = Callable[[], BaseForecaster]


def _has(module: str) -> bool:
    try:
        return importlib.util.find_spec(module) is not None
    except Exception:  # noqa: BLE001
        return False


def _make_arima() -> BaseForecaster:
    from backend.app.ml.models.arima import ARIMAForecaster

    return ARIMAForecaster()


def _make_prophet() -> BaseForecaster:
    from backend.app.ml.models.prophet_model import ProphetForecaster

    return ProphetForecaster()


def _make_lstm() -> BaseForecaster:
    from backend.app.ml.models.lstm import LSTMForecaster

    return LSTMForecaster()


_CANDIDATES: dict[str, tuple[str, Factory]] = {
    # name -> (required-module, factory)
    "linear": ("sklearn", make_linear),
    "random_forest": ("sklearn", make_random_forest),
    "xgboost": ("xgboost", make_xgboost),
    "lightgbm": ("lightgbm", make_lightgbm),
    "arima": ("statsmodels", _make_arima),
    "prophet": ("prophet", _make_prophet),
    "lstm": ("torch", _make_lstm),
}


class ModelRegistry:
    """Create forecaster instances by name; reflects environment availability."""

    def __init__(self) -> None:
        self._available: dict[str, Factory] = {}
        for name, (module, factory) in _CANDIDATES.items():
            if _has(module):
                self._available[name] = factory
            else:
                log.info("model %s unavailable (missing optional dependency: %s)", name, module)

    def available(self) -> list[str]:
        return list(self._available.keys())

    def is_available(self, name: str) -> bool:
        return name in self._available

    def create(self, name: str) -> BaseForecaster:
        if name not in self._available:
            raise KeyError(f"model '{name}' is not registered/available; available={self.available()}")
        return self._available[name]()

    def default_candidates(self) -> list[str]:
        """Sensible default zoo ordered by expected quality/cost (docs/ml_pipeline.md §4)."""
        preference = ["xgboost", "lightgbm", "random_forest", "linear", "arima", "prophet", "lstm"]
        return [m for m in preference if m in self._available]
