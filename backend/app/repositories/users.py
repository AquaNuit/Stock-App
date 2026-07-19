"""User / watchlist / search-history persistence (header-identity MVP, ADR-0011)."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import delete, select

from backend.app.database.models import SearchHistory, Stock, User, Watchlist, WatchlistItem
from backend.app.repositories.base import Repository

DEFAULT_USER = "guest"


class UserRepository(Repository[User]):
    model = User

    def get_or_create(self, external_id: str) -> User:
        ext = (external_id or DEFAULT_USER).strip() or DEFAULT_USER
        user = self.session.scalar(select(User).where(User.external_id == ext))
        if user is None:
            user = self.add(User(external_id=ext, display_name=ext))
        return user


class WatchlistRepository(Repository[Watchlist]):
    model = Watchlist

    def default_list_for(self, user: User) -> Watchlist:
        wl = self.session.scalar(select(Watchlist).where(Watchlist.user_id == user.id, Watchlist.name == "Default"))
        if wl is None:
            wl = self.add(Watchlist(user_id=user.id, name="Default"))
        return wl

    def items(self, wl: Watchlist) -> list[Stock]:
        stmt = (
            select(Stock)
            .join(WatchlistItem, WatchlistItem.stock_id == Stock.id)
            .where(WatchlistItem.watchlist_id == wl.id)
            .order_by(Stock.symbol)
        )
        return list(self.session.scalars(stmt))

    def add_symbol(self, wl: Watchlist, stock: Stock) -> bool:
        existing = self.session.scalar(
            select(WatchlistItem).where(
                WatchlistItem.watchlist_id == wl.id, WatchlistItem.stock_id == stock.id
            )
        )
        if existing:
            return False
        self.session.add(WatchlistItem(watchlist_id=wl.id, stock_id=stock.id))
        self.session.flush()
        return True

    def remove_symbol(self, wl: Watchlist, stock: Stock) -> bool:
        result = self.session.execute(
            delete(WatchlistItem).where(
                WatchlistItem.watchlist_id == wl.id, WatchlistItem.stock_id == stock.id
            )
        )
        self.session.flush()
        return bool(result.rowcount)


class SearchRepository(Repository[SearchHistory]):
    model = SearchHistory

    def record(self, user: User, query: str, matched_symbol: str = "") -> None:
        self.session.add(SearchHistory(user_id=user.id, query=query[:120], matched_symbol=matched_symbol))
        self.session.flush()

    def recent(self, user: User, *, limit: int = 10) -> list[SearchHistory]:
        stmt = (
            select(SearchHistory)
            .where(SearchHistory.user_id == user.id)
            .order_by(SearchHistory.created_at.desc())
            .limit(limit)
        )
        rows = list(self.session.scalars(stmt))
        # De-duplicate consecutive identical queries for display.
        seen: set[str] = set()
        out = []
        for r in rows:
            key = r.query.upper()
            if key not in seen:
                seen.add(key)
                out.append(r)
        return out

    def prune_older_than(self, days: int = 90) -> int:
        from datetime import timedelta

        cutoff = datetime.now(UTC) - timedelta(days=days)
        result = self.session.execute(delete(SearchHistory).where(SearchHistory.created_at < cutoff))
        self.session.flush()
        return int(result.rowcount or 0)
