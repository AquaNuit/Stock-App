"""v1 route aggregation."""

from __future__ import annotations

from fastapi import APIRouter

from backend.app.api.v1.routes import (
    export,
    health,
    indicators,
    insights,
    market,
    predictions,
    stocks,
    watchlist,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(market.router)
api_router.include_router(stocks.router)
api_router.include_router(indicators.router)
api_router.include_router(predictions.router)
api_router.include_router(insights.router)
api_router.include_router(watchlist.router)
api_router.include_router(export.router)
