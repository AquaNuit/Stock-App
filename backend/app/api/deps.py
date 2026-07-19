"""Dependency-injection composition root (docs/architecture.md §1).

Only this module wires concrete implementations together. Services receive
their collaborators via constructors; routers receive services via ``Depends``.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from backend.app.cache import CacheManager
from backend.app.core.config import Settings, get_settings
from backend.app.database.session import get_session_factory
from backend.app.providers import ProviderChain, default_chain
from backend.app.services.indicator_service import IndicatorService
from backend.app.services.insights_service import InsightsService
from backend.app.services.market_data import MarketDataService
from backend.app.services.prediction_service import PredictionService
from backend.app.services.stock_service import StockService
from backend.app.services.watchlist_service import WatchlistService

# -- singletons -------------------------------------------------------------

_settings: Settings = get_settings()
_cache: CacheManager | None = None
_chain: ProviderChain | None = None


def get_cache() -> CacheManager:
    global _cache
    if _cache is None:
        _cache = CacheManager(_settings)
    return _cache


def get_chain() -> ProviderChain:
    global _chain
    if _chain is None:
        _chain = default_chain(_settings, get_cache())
    return _chain


def reset_singletons() -> None:
    """Testing hook."""
    global _cache, _chain
    _cache = None
    _chain = None


# -- per-request ------------------------------------------------------------

def get_db() -> Iterator[Session]:
    session = get_session_factory(_settings)()
    try:
        yield session
    finally:
        session.close()


DbDep = Annotated[Session, Depends(get_db)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
CacheDep = Annotated[CacheManager, Depends(get_cache)]
ChainDep = Annotated[ProviderChain, Depends(get_chain)]


def get_stock_service(db: DbDep, chain: ChainDep) -> StockService:
    return StockService(db, chain)


def get_market_service(chain: ChainDep, cache: CacheDep) -> MarketDataService:
    return MarketDataService(chain, cache, _settings)


def get_prediction_service(db: DbDep, stock_svc: Annotated[StockService, Depends(get_stock_service)]) -> PredictionService:
    return PredictionService(db, stock_svc, settings=_settings)


def get_indicator_service(stock_svc: Annotated[StockService, Depends(get_stock_service)]) -> IndicatorService:
    return IndicatorService(stock_svc)


def get_insights_service(stock_svc: Annotated[StockService, Depends(get_stock_service)]) -> InsightsService:
    return InsightsService(stock_svc)


def get_watchlist_service(db: DbDep, chain: ChainDep) -> WatchlistService:
    return WatchlistService(db, chain)


def get_user_id(x_user_id: Annotated[str | None, Header()] = None) -> str:
    """Header-identity resolution (ADR-0011)."""
    return (x_user_id or "guest").strip()[:64] or "guest"


UserDep = Annotated[str, Depends(get_user_id)]

StockServiceDep = Annotated[StockService, Depends(get_stock_service)]
MarketServiceDep = Annotated[MarketDataService, Depends(get_market_service)]
PredictionServiceDep = Annotated[PredictionService, Depends(get_prediction_service)]
IndicatorServiceDep = Annotated[IndicatorService, Depends(get_indicator_service)]
InsightsServiceDep = Annotated[InsightsService, Depends(get_insights_service)]
WatchlistServiceDep = Annotated[WatchlistService, Depends(get_watchlist_service)]
