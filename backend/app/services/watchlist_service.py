"""Watchlist + recent-searches use-cases (header-identity users, ADR-0011)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app.core.logging import get_logger
from backend.app.providers import ProviderChain
from backend.app.repositories import (
    PredictionRepository,
    SearchRepository,
    StockRepository,
    UserRepository,
    WatchlistRepository,
)
from backend.app.schemas.users import SearchHistoryRow, WatchlistResponse, WatchlistRow
from backend.app.services.stock_service import StockService

log = get_logger(__name__)


class WatchlistService:
    def __init__(self, session: Session, chain: ProviderChain):
        self.session = session
        self.chain = chain
        self.users = UserRepository(session)
        self.watchlists = WatchlistRepository(session)
        self.stocks = StockRepository(session)
        self.searches = SearchRepository(session)
        self.predictions = PredictionRepository(session)
        self.stock_service = StockService(session, chain)

    # ---------------------------------------------------------------- watchlist
    def list(self, external_user: str) -> WatchlistResponse:
        user = self.users.get_or_create(external_user)
        wl = self.watchlists.default_list_for(user)
        rows: list[WatchlistRow] = []
        for stock in self.watchlists.items(wl):
            price = change_pct = None
            try:
                q = self.chain.get_quote(stock.symbol)
                price, change_pct = q.price, q.change_pct
            except Exception as exc:  # noqa: BLE001
                log.debug("quote failed for %s: %s", stock.symbol, exc)
            item = next(
                (i for i in wl.items if i.stock_id == stock.id), None
            )
            batch = self.predictions.latest_batch(stock.id)
            fc = round(sum(p.expected_change_pct for p in batch) / len(batch), 2) if batch else None
            rows.append(
                WatchlistRow(
                    symbol=stock.symbol, company_name=stock.company_name,
                    price=price, change_pct=change_pct,
                    added_at=item.added_at if item else user.created_at,
                    latest_forecast_change_pct=fc,
                )
            )
        return WatchlistResponse(user=user.external_id, count=len(rows), items=rows)

    def add(self, external_user: str, symbol: str) -> WatchlistResponse:
        user = self.users.get_or_create(external_user)
        stock = self.stock_service._require_stock(symbol)
        wl = self.watchlists.default_list_for(user)
        self.watchlists.add_symbol(wl, stock)
        self.session.commit()
        return self.list(external_user)

    def remove(self, external_user: str, symbol: str) -> WatchlistResponse:
        user = self.users.get_or_create(external_user)
        stock = self.stocks.by_symbol(symbol.upper())
        wl = self.watchlists.default_list_for(user)
        if stock is not None:
            self.watchlists.remove_symbol(wl, stock)
            self.session.commit()
        return self.list(external_user)

    # ---------------------------------------------------------------- searches
    def record_search(self, external_user: str, query: str, matched_symbol: str = "") -> None:
        user = self.users.get_or_create(external_user)
        self.searches.record(user, query, matched_symbol)
        self.session.commit()

    def recent_searches(self, external_user: str, limit: int = 10) -> list[SearchHistoryRow]:
        user = self.users.get_or_create(external_user)
        return [
            SearchHistoryRow(query=r.query, matched_symbol=r.matched_symbol, created_at=r.created_at)
            for r in self.searches.recent(user, limit=limit)
        ]
